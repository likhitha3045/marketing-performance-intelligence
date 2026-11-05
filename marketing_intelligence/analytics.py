from __future__ import annotations

import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from marketing_intelligence.data_pipeline import TABLE_FILES, load_database


def load_frames(data_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    database = load_database(data_dir=data_dir) if data_dir else load_database()
    return _load_frames_from_database(database)


def load_uploaded_frames(files: Mapping[str, bytes]) -> dict[str, pd.DataFrame]:
    """Validate a complete set of project CSVs and load the frames without persisting uploads."""
    expected_names = set(TABLE_FILES.values())
    supplied_names = set(files)
    unexpected_names = supplied_names - expected_names
    missing_names = expected_names - supplied_names
    if unexpected_names:
        raise ValueError(f"Unsupported CSV file(s): {', '.join(sorted(unexpected_names))}.")
    if missing_names:
        raise ValueError(f"Missing required CSV file(s): {', '.join(sorted(missing_names))}.")

    with tempfile.TemporaryDirectory(prefix="marketing-upload-") as directory:
        data_dir = Path(directory)
        for filename, content in files.items():
            (data_dir / filename).write_bytes(content)
        database = load_database(data_dir=data_dir)
        return _load_frames_from_database(database)


def _load_frames_from_database(database: Path) -> dict[str, pd.DataFrame]:
    with closing(sqlite3.connect(database)) as connection:
        frames = {
            "campaigns": pd.read_sql_query(
                """
                SELECT c.*, ch.channel_name
                FROM campaigns c JOIN channels ch USING (channel_id)
                """,
                connection,
            ),
            "customers": pd.read_sql_query("SELECT * FROM customers", connection),
            "spend": pd.read_sql_query("SELECT * FROM marketing_spend", connection),
            "leads": pd.read_sql_query("SELECT * FROM leads", connection),
            "conversions": pd.read_sql_query("SELECT * FROM conversions", connection),
            "products": pd.read_sql_query("SELECT * FROM products", connection),
            "transactions": pd.read_sql_query("SELECT * FROM transactions", connection),
        }
    for frame_name, column in (
        ("campaigns", "start_date"),
        ("campaigns", "end_date"),
        ("customers", "signup_date"),
        ("spend", "activity_date"),
        ("leads", "lead_date"),
        ("conversions", "conversion_date"),
        ("transactions", "transaction_date"),
    ):
        frames[frame_name][column] = pd.to_datetime(frames[frame_name][column], errors="raise")
    return frames


def campaign_performance(
    spend: pd.DataFrame,
    conversions: pd.DataFrame,
    campaigns: pd.DataFrame,
) -> pd.DataFrame:
    spend_totals = (
        spend.groupby("campaign_id", as_index=False)
        .agg(spend=("spend", "sum"), impressions=("impressions", "sum"), clicks=("clicks", "sum"))
    )
    conversion_totals = (
        conversions.groupby("campaign_id", as_index=False)
        .agg(revenue=("revenue", "sum"), conversions=("conversion_id", "count"))
    )
    performance = campaigns.merge(spend_totals, on="campaign_id", how="left").merge(
        conversion_totals, on="campaign_id", how="left"
    )
    for column in ("spend", "impressions", "clicks", "revenue", "conversions"):
        performance[column] = performance[column].fillna(0)
    performance["ctr"] = _percent(performance["clicks"], performance["impressions"])
    performance["cpc"] = _divide(performance["spend"], performance["clicks"])
    performance["cpa"] = _divide(performance["spend"], performance["conversions"])
    performance["conversion_rate"] = _percent(performance["conversions"], performance["clicks"])
    performance["roas"] = _divide(performance["revenue"], performance["spend"])
    performance["budget_used"] = _percent(performance["spend"], performance["budget"])
    return performance


def channel_performance(
    spend: pd.DataFrame,
    conversions: pd.DataFrame,
    campaigns: pd.DataFrame,
) -> pd.DataFrame:
    channel_lookup = campaigns[["campaign_id", "channel_name"]].drop_duplicates()
    if "channel_name" not in spend.columns:
        spend = spend.merge(channel_lookup, on="campaign_id", how="left")
    if "channel_name" not in conversions.columns:
        conversions = conversions.merge(channel_lookup, on="campaign_id", how="left")
    spend_by_channel = (
        spend.groupby("channel_name", as_index=False)
        .agg(spend=("spend", "sum"), impressions=("impressions", "sum"), clicks=("clicks", "sum"))
    )
    conversion_by_channel = (
        conversions.groupby("channel_name", as_index=False)
        .agg(revenue=("revenue", "sum"), conversions=("conversion_id", "count"))
    )
    result = spend_by_channel.merge(conversion_by_channel, on="channel_name", how="left").fillna(
        {"revenue": 0, "conversions": 0}
    )
    result["ctr"] = _percent(result["clicks"], result["impressions"])
    result["cpc"] = _divide(result["spend"], result["clicks"])
    result["cpa"] = _divide(result["spend"], result["conversions"])
    result["conversion_rate"] = _percent(result["conversions"], result["clicks"])
    result["roas"] = _divide(result["revenue"], result["spend"])
    return result.sort_values("roas", ascending=False)


def funnel_totals(spend: pd.DataFrame, leads: pd.DataFrame, conversions: pd.DataFrame) -> pd.DataFrame:
    stages = [
        ("Impressions", int(spend["impressions"].sum())),
        ("Clicks", int(spend["clicks"].sum())),
        ("Leads", int(leads["lead_id"].nunique())),
        ("Conversions", int(conversions["conversion_id"].nunique())),
    ]
    return pd.DataFrame(stages, columns=["stage", "count"])


def build_analyst_findings(
    performance: pd.DataFrame,
    channels: pd.DataFrame,
    funnel: pd.DataFrame,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    active_campaigns = performance[performance["spend"] > 0]
    converting_channels = channels[channels["conversions"] > 0]

    if not converting_channels.empty:
        best = converting_channels.loc[converting_channels["roas"].idxmax()]
        findings.append(
            {
                "title": f"{best['channel_name']} has the highest observed channel ROAS",
                "evidence": f"{best['roas']:.2f}x ROAS from {int(best['conversions']):,} conversions and ₹{best['spend']:,.0f} spend.",
                "action": "Check performance by date and test any budget changes incrementally; historical ROAS does not establish causal lift.",
                "priority": "Opportunity",
            }
        )

    if len(converting_channels) > 1:
        lowest = converting_channels.loc[converting_channels["roas"].idxmin()]
        findings.append(
            {
                "title": f"Review {lowest['channel_name']} before shifting more budget",
                "evidence": f"Observed ROAS is {lowest['roas']:.2f}x across {int(lowest['conversions']):,} conversions.",
                "action": "Inspect campaign mix, attribution, and conversion quality before deciding whether to optimize or reduce spend.",
                "priority": "Review",
            }
        )

    overspent = active_campaigns[active_campaigns["spend"] > active_campaigns["budget"]]
    if not overspent.empty:
        row = overspent.nlargest(1, "budget_used").iloc[0]
        findings.append(
            {
                "title": f"{row['campaign_name']} exceeded its budget",
                "evidence": f"₹{row['spend']:,.0f} spend against ₹{row['budget']:,.0f} budget ({row['budget_used']:.1f}% used).",
                "action": "Confirm the budget period and review pacing or approved budget changes.",
                "priority": "Action needed",
            }
        )

    if len(active_campaigns) > 1:
        median_cpa = active_campaigns.loc[active_campaigns["conversions"] > 0, "cpa"].median()
        high_cpa = active_campaigns[
            (active_campaigns["conversions"] > 0)
            & (active_campaigns["cpa"] > median_cpa * 1.4)
        ]
        if not high_cpa.empty:
            row = high_cpa.nlargest(1, "cpa").iloc[0]
            findings.append(
                {
                    "title": f"{row['campaign_name']} has an above-median CPA",
                    "evidence": f"CPA is ₹{row['cpa']:,.0f}, compared with a portfolio campaign median of ₹{median_cpa:,.0f}.",
                    "action": "Investigate targeting, creative, and conversion volume before changing its budget.",
                    "priority": "Review",
                }
            )

    if len(funnel) > 1:
        stages = funnel.reset_index(drop=True)
        prior_count = float(stages.iloc[0]["count"])
        dropoffs = []
        for index in range(1, len(stages)):
            current_count = float(stages.iloc[index]["count"])
            if prior_count > 0:
                dropoffs.append((1 - current_count / prior_count, index, prior_count, current_count))
            prior_count = current_count
        if dropoffs:
            largest_drop = max(dropoffs, key=lambda item: item[0])
            fraction, index, prior, current = largest_drop
            findings.append(
                {
                    "title": f"Largest measured funnel drop is {stages.iloc[index]['stage']}",
                    "evidence": f"{fraction * 100:.1f}% drop from {int(prior):,} {stages.iloc[index - 1]['stage'].lower()} to {int(current):,} {stages.iloc[index]['stage'].lower()}.",
                    "action": "Validate stage definitions and tracking, then investigate this transition before optimizing earlier stages.",
                    "priority": "Investigate",
                }
            )

    if not findings:
        findings.append(
            {
                "title": "More data is needed for comparative findings",
                "evidence": "The selected filters contain no comparable converting channels or campaign activity.",
                "action": "Widen the date range or select a campaign with recorded marketing activity and conversions.",
                "priority": "Informational",
            }
        )
    return findings


def _linear_forecast(values: np.ndarray, periods: int) -> tuple[np.ndarray, float]:
    x_values = np.arange(len(values), dtype=float)
    slope, intercept = np.polyfit(x_values, values, 1)
    fitted = slope * x_values + intercept
    residual_error = float(np.sqrt(np.mean(np.square(values - fitted)))) if len(values) > 2 else 0.0
    future_x = np.arange(len(values), len(values) + periods, dtype=float)
    predictions = np.maximum(0, slope * future_x + intercept)
    return predictions, residual_error


def forecast_monthly_trend(
    monthly: pd.DataFrame,
    metric: str,
    horizon: int = 3,
) -> tuple[pd.DataFrame, dict[str, float] | None]:
    """Create a simple linear trend forecast and a held-out two-month error summary."""
    if metric not in monthly.columns:
        raise ValueError(f"Unknown forecast metric: {metric}")
    if horizon < 1 or horizon > 12:
        raise ValueError("Forecast horizon must be between 1 and 12 months.")

    history = monthly[["month", metric]].dropna().sort_values("month").copy()
    if not pd.api.types.is_datetime64_any_dtype(history["month"]):
        history["month"] = pd.to_datetime(history["month"], errors="raise")
    history[metric] = pd.to_numeric(history[metric], errors="coerce")
    history = history.dropna(subset=[metric])
    if len(history) < 4:
        raise ValueError("At least four complete months are required to forecast.")
    if (history[metric] < 0).any():
        raise ValueError("Forecast metrics cannot contain negative values.")

    values = history[metric].to_numpy(dtype=float)
    forecast_values, residual_error = _linear_forecast(values, horizon)
    last_month = history["month"].max()
    forecast_months = pd.date_range(last_month + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    forecast = pd.DataFrame(
        {
            "month": forecast_months,
            "forecast": forecast_values,
            "lower": np.maximum(0, forecast_values - 1.96 * residual_error),
            "upper": forecast_values + 1.96 * residual_error,
        }
    )

    backtest: dict[str, float] | None = None
    if len(values) >= 6:
        train_values = values[:-2]
        holdout_actual = values[-2:]
        holdout_predictions, _ = _linear_forecast(train_values, len(holdout_actual))
        absolute_errors = np.abs(holdout_actual - holdout_predictions)
        nonzero_actuals = holdout_actual != 0
        mape = (
            float(np.mean(absolute_errors[nonzero_actuals] / holdout_actual[nonzero_actuals]) * 100)
            if nonzero_actuals.any()
            else 0.0
        )
        backtest = {
            "mae": float(np.mean(absolute_errors)),
            "mape": mape,
        }
    return forecast, backtest


def build_recommendations(
    performance: pd.DataFrame,
    channels: pd.DataFrame,
    conversions: pd.DataFrame,
) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    active_campaigns = performance[performance["spend"] > 0]
    portfolio_cpa = (
        active_campaigns.loc[active_campaigns["conversions"] > 0, "cpa"].median()
        if (active_campaigns["conversions"] > 0).any()
        else 0
    )
    portfolio_roas = (
        active_campaigns["revenue"].sum() / active_campaigns["spend"].sum()
        if active_campaigns["spend"].sum() > 0
        else 0
    )

    overspent = active_campaigns[active_campaigns["spend"] > active_campaigns["budget"]]
    for row in overspent.nlargest(2, "budget_used").itertuples():
        recommendations.append(
            _recommendation(
                f"budget-overrun-{row.campaign_id}",
                "Budget control",
                f"{row.campaign_name} exceeded its campaign budget.",
                f"Spend is {row.budget_used:.0f}% of budget (₹{row.spend:,.0f} of ₹{row.budget:,.0f}).",
                "Review pacing and reallocate remaining spend to campaigns within budget.",
                "Avoid uncontrolled overspend and protect campaign efficiency.",
                "High",
            )
        )

    high_cpa = active_campaigns[
        (active_campaigns["conversions"] > 0)
        & (active_campaigns["cpa"] > portfolio_cpa * 1.4)
    ].nlargest(2, "cpa")
    for row in high_cpa.itertuples():
        recommendations.append(
            _recommendation(
                f"high-cpa-{row.campaign_id}",
                "Campaign optimisation",
                f"{row.campaign_name} has a higher acquisition cost than the portfolio.",
                f"CPA is ₹{row.cpa:,.0f} versus portfolio median ₹{portfolio_cpa:,.0f}.",
                "Review audience targeting, search terms, and creative before increasing budget.",
                "Potentially lower cost per acquired customer.",
                "High",
            )
        )

    strong_channels = channels[
        (channels["spend"] > 0)
        & (channels["conversions"] >= 10)
        & (channels["roas"] > portfolio_roas * 1.15)
    ].nlargest(1, "roas")
    for row in strong_channels.itertuples():
        recommendations.append(
            _recommendation(
                f"scale-channel-{_slug(row.channel_name)}",
                "Budget opportunity",
                f"{row.channel_name} is generating above-portfolio return.",
                f"ROAS is {row.roas:.2f}x against portfolio {portfolio_roas:.2f}x, with {row.conversions:.0f} conversions.",
                "Test a measured budget increase and monitor marginal CPA.",
                "Grow revenue while validating that efficiency holds at higher spend.",
                "Medium",
            )
        )

    conversion_counts = conversions.groupby("customer_id")["conversion_id"].count()
    repeat_rate = (conversion_counts > 1).mean() * 100 if len(conversion_counts) else 0
    if len(conversion_counts) >= 20 and repeat_rate < 20:
        recommendations.append(
            _recommendation(
                "customer-repeat-purchase",
                "Retention opportunity",
                "Repeat conversion activity is limited in the selected period.",
                f"{repeat_rate:.1f}% of converting customers have more than one conversion.",
                "Test a post-purchase email or retention campaign for recently acquired customers.",
                "Improve repeat engagement and customer lifetime value.",
                "Medium",
            )
        )

    if not recommendations:
        recommendations.append(
            _recommendation(
                "portfolio-monitor",
                "Portfolio health",
                "No campaign is currently breaching the configured CPA or budget thresholds.",
                f"Portfolio ROAS is {portfolio_roas:.2f}x and median CPA is ₹{portfolio_cpa:,.0f}.",
                "Keep monitoring performance and compare marginal results before reallocating budget.",
                "Maintain efficiency while preserving room to react to performance changes.",
                "Low",
            )
        )
    return recommendations


def recommendation_actions(database: Path) -> dict[str, dict[str, str]]:
    import sqlite3

    with sqlite3.connect(database) as connection:
        rows = connection.execute(
            "SELECT recommendation_key, status, manager_decision FROM recommendation_actions"
        ).fetchall()
    return {key: {"status": status, "decision": decision} for key, status, decision in rows}


def save_recommendation_action(database: Path, key: str, status: str, decision: str) -> None:
    if status not in {"Pending", "In Progress", "Completed"}:
        raise ValueError(f"Unsupported recommendation status: {status}")
    import sqlite3

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO recommendation_actions (recommendation_key, status, manager_decision, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(recommendation_key) DO UPDATE SET
                status = excluded.status,
                manager_decision = excluded.manager_decision,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, status, decision.strip()),
        )


def _recommendation(
    key: str,
    category: str,
    problem: str,
    evidence: str,
    action: str,
    benefit: str,
    priority: str,
) -> dict[str, str]:
    return {
        "key": key,
        "category": category,
        "problem": problem,
        "evidence": evidence,
        "action": action,
        "benefit": benefit,
        "priority": priority,
    }


def _slug(value: str) -> str:
    return "-".join(value.lower().split())


def _divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.div(denominator.where(denominator != 0)).fillna(0)


def _percent(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return _divide(numerator, denominator) * 100
