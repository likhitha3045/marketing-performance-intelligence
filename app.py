from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from marketing_intelligence.analytics import (
    build_recommendations,
    campaign_performance,
    channel_performance,
    build_analyst_findings,
    funnel_totals,
    load_frames,
    load_uploaded_frames,
    forecast_monthly_trend,
    recommendation_actions,
    save_recommendation_action,
)
from marketing_intelligence.data_pipeline import load_database

st.set_page_config(
    page_title="Marketing Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink:#14213d; --muted:#758198; --line:#e7ebf2; --blue:#315eea; }
    html, body, [class*="css"] { font-family: "Segoe UI", Arial, sans-serif; }
    .stApp { background: #f7f8fb; }
    h1, h2, h3 { font-family: "Segoe UI", Arial, sans-serif; color: var(--ink); letter-spacing: -0.035em; }
    h1 { font-size: 2rem; }
    [data-testid="stSidebar"] { background: #101b32; }
    [data-testid="stSidebar"] * { color: #eef2ff; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #9daac2; }
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-testid="stDateInput"] *,
    [data-testid="stSidebar"] [data-testid="stTextInput"] *,
    [data-testid="stSidebar"] [data-testid="stNumberInput"] *,
    [data-testid="stSidebar"] [data-baseweb="input"] *,
    [data-testid="stSidebar"] [data-baseweb="datepicker"] * {
      color: #000000 !important;
      -webkit-text-fill-color: #000000 !important;
      opacity: 1 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"],
    [data-testid="stSidebar"] [data-baseweb="input"] > div,
    [data-testid="stSidebar"] [data-testid="stDateInput"] > div > div {
      background-color: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] svg {
      fill: #000000 !important;
    }
    [data-testid="stSidebar"] input::placeholder {
      color: #000000 !important;
      -webkit-text-fill-color: #000000 !important;
      opacity: 1 !important;
    }
    [data-testid="stMetric"] {
      background: white; border: 1px solid var(--line); padding: 18px 20px;
      border-radius: 14px; box-shadow: 0 2px 8px rgba(20,33,61,.03);
    }
    [data-testid="stMetricLabel"] { color: var(--muted); font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--ink); font-family: "Segoe UI", Arial, sans-serif; }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; }
    .eyebrow { color:#71809b; font-size:.78rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
    .card { background:white; border:1px solid var(--line); border-radius:14px; padding:18px 20px; margin:8px 0 12px; }
    .muted { color:var(--muted); }
    .pill { display:inline-block; padding:4px 9px; border-radius:99px; font-size:.76rem; font-weight:700; background:#edf2ff; color:#315eea; }
    div[data-testid="stButton"] > button { border-radius:9px; font-weight:600; }
    </style>
    """,
    unsafe_allow_html=True,
)

PAGE_NAMES = [
    "Executive Overview",
    "Data Analyst Findings",
    "Campaign Analytics",
    "Channel Performance",
    "Customer Insights",
    "Conversion Funnel",
    "Revenue & ROI",
    "Forecast & Trends",
    "Growth Opportunities",
    "Recommendations",
    "Reports & Export",
]
CURRENCY = "₹"


@st.cache_data(show_spinner=False)
def get_project_frames() -> dict[str, pd.DataFrame]:
    return load_frames()


sample_frames = get_project_frames()
upload_required_files = {
    "channels.csv",
    "campaigns.csv",
    "customers.csv",
    "marketing_spend.csv",
    "leads.csv",
    "conversions.csv",
    "products.csv",
    "transactions.csv",
}

st.sidebar.markdown("## Growth intelligence")
st.sidebar.caption("Marketing performance workspace")
uploaded_files = st.sidebar.file_uploader(
    "Upload your project CSVs",
    type=["csv"],
    accept_multiple_files=True,
    help="Upload all eight CSVs using the filenames and columns in the README.",
)
data_is_uploaded = False
frames = sample_frames
if uploaded_files:
    uploaded_names = [Path(file.name).name for file in uploaded_files]
    duplicate_uploads = sorted(
        name for name in set(uploaded_names) if uploaded_names.count(name) > 1
    )
    uploaded_by_name = {
        Path(file.name).name: file.getvalue() for file in uploaded_files
    }
    missing_uploads = upload_required_files - set(uploaded_by_name)
    if duplicate_uploads:
        st.sidebar.error(
            f"Remove duplicate upload(s): {', '.join(duplicate_uploads)}. The sample dataset remains selected."
        )
    elif missing_uploads:
        st.sidebar.warning(
            "Upload all eight required CSV files. The sample dataset is still selected."
        )
    else:
        try:
            frames = load_uploaded_frames(uploaded_by_name)
        except (
            FileNotFoundError,
            ValueError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            UnicodeDecodeError,
        ) as error:
            st.sidebar.error(f"Could not use uploaded data: {error}")
            st.sidebar.caption("The sample dataset remains selected.")
        else:
            data_is_uploaded = True
            st.sidebar.success("Uploaded data validated for this session.")
else:
    st.sidebar.caption("Using the included synthetic sample data.")

database = load_database()


def title_block(title: str, subtitle: str) -> None:
    st.markdown(f'<p class="eyebrow">MARKETING PERFORMANCE & GROWTH INTELLIGENCE</p>', unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)
    st.caption("Data source: uploaded CSVs" if data_is_uploaded else "Data source: synthetic sample")


def money(value: float) -> str:
    return f"{CURRENCY}{value:,.0f}"


def safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def sidebar_filters(data: dict[str, pd.DataFrame]) -> tuple[str, pd.Timestamp, pd.Timestamp, str, str, str]:
    page = st.sidebar.radio("Workspace", PAGE_NAMES, label_visibility="collapsed")
    st.sidebar.markdown("---")
    min_date = data["spend"]["activity_date"].min().date()
    max_date = data["spend"]["activity_date"].max().date()
    selected_dates = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    elif isinstance(selected_dates, tuple) and len(selected_dates) == 1:
        start_date = end_date = selected_dates[0]
    else:
        start_date = end_date = selected_dates

    channel_names = ["All channels", *sorted(data["campaigns"]["channel_name"].unique())]
    channel = st.sidebar.selectbox("Channel", channel_names)
    available_campaigns = data["campaigns"]
    if channel != "All channels":
        available_campaigns = available_campaigns[available_campaigns["channel_name"] == channel]
    campaign_names = ["All campaigns", *sorted(available_campaigns["campaign_name"].unique())]
    campaign = st.sidebar.selectbox("Campaign", campaign_names)
    segments = ["All segments", *sorted(data["customers"]["segment"].unique())]
    segment = st.sidebar.selectbox("Customer segment", segments)
    regions = ["All regions", *sorted(data["customers"]["region"].unique())]
    region = st.sidebar.selectbox("Customer region", regions)
    st.sidebar.markdown("---")
    st.sidebar.caption("Region and segment filters apply to Customer Insights only.")
    return (
        page,
        pd.Timestamp(start_date),
        pd.Timestamp(end_date),
        channel,
        campaign,
        f"{segment}|{region}",
    )


page, start_date, end_date, selected_channel, selected_campaign, customer_filter = sidebar_filters(frames)
selected_segment, selected_region = customer_filter.split("|", maxsplit=1)


def filtered_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    campaign_frame = frames["campaigns"].copy()
    spend = frames["spend"].merge(campaign_frame, on="campaign_id", how="left")
    conversions = frames["conversions"].merge(campaign_frame, on="campaign_id", how="left").merge(
        frames["customers"], on="customer_id", how="left"
    )
    leads = frames["leads"].merge(campaign_frame, on="campaign_id", how="left").merge(
        frames["customers"], on="customer_id", how="left"
    )
    for frame, date_column in ((spend, "activity_date"), (conversions, "conversion_date"), (leads, "lead_date")):
        frame.drop(frame[(frame[date_column] < start_date) | (frame[date_column] > end_date)].index, inplace=True)
    if selected_channel != "All channels":
        spend = spend[spend["channel_name"] == selected_channel]
        conversions = conversions[conversions["channel_name"] == selected_channel]
        leads = leads[leads["channel_name"] == selected_channel]
        campaign_frame = campaign_frame[campaign_frame["channel_name"] == selected_channel]
    if selected_campaign != "All campaigns":
        spend = spend[spend["campaign_name"] == selected_campaign]
        conversions = conversions[conversions["campaign_name"] == selected_campaign]
        leads = leads[leads["campaign_name"] == selected_campaign]
        campaign_frame = campaign_frame[campaign_frame["campaign_name"] == selected_campaign]
    return spend, conversions, leads, campaign_frame


spend_df, conversions_df, leads_df, campaigns_df = filtered_data()
customer_conversions_df = conversions_df
if selected_segment != "All segments":
    customer_conversions_df = customer_conversions_df[customer_conversions_df["segment"] == selected_segment]
if selected_region != "All regions":
    customer_conversions_df = customer_conversions_df[customer_conversions_df["region"] == selected_region]
performance = campaign_performance(spend_df, conversions_df, campaigns_df)
channels = channel_performance(spend_df, conversions_df, campaigns_df)

if selected_segment != "All segments" or selected_region != "All regions":
    st.info("Customer segment and region filters apply only to Customer Insights. Campaign, funnel, and ROI metrics retain the full selected campaign/date scope so spend and conversions remain comparable.")


def show_kpis() -> None:
    revenue = float(conversions_df["revenue"].sum())
    spend = float(spend_df["spend"].sum())
    conversion_count = int(conversions_df["conversion_id"].nunique())
    customer_count = int(conversions_df["customer_id"].nunique())
    click_count = int(spend_df["clicks"].sum())
    conversion_rate = safe_ratio(conversion_count, click_count) * 100
    roas = safe_ratio(revenue, spend)
    columns = st.columns(6)
    metrics = [
        ("Total revenue", money(revenue)),
        ("Marketing spend", money(spend)),
        ("Customers acquired", f"{customer_count:,}"),
        ("Conversions", f"{conversion_count:,}"),
        ("Conversion rate", f"{conversion_rate:.2f}%"),
        ("ROAS", f"{roas:.2f}x"),
    ]
    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)


def monthly_performance() -> pd.DataFrame:
    spend_monthly = spend_df.assign(month=spend_df["activity_date"].dt.to_period("M").dt.to_timestamp())
    revenue_monthly = conversions_df.assign(month=conversions_df["conversion_date"].dt.to_period("M").dt.to_timestamp())
    left = spend_monthly.groupby("month", as_index=False).agg(spend=("spend", "sum"))
    right = revenue_monthly.groupby("month", as_index=False).agg(revenue=("revenue", "sum"))
    return left.merge(right, on="month", how="outer").fillna(0).sort_values("month")


def show_table(frame: pd.DataFrame, columns: list[str], formatters: dict[str, str] | None = None) -> None:
    visible = frame[[column for column in columns if column in frame.columns]].copy()
    if formatters:
        st.dataframe(visible.style.format(formatters, na_rep="—"), width="stretch", hide_index=True)
    else:
        st.dataframe(visible, width="stretch", hide_index=True)


def render_overview() -> None:
    title_block("Executive overview", "A decision-ready snapshot of acquisition, revenue, and marketing efficiency.")
    show_kpis()
    trend, channels_col = st.columns([1.55, 1])
    with trend:
        st.subheader("Revenue and spend trend")
        monthly = monthly_performance()
        if not monthly.empty:
            figure = go.Figure()
            figure.add_trace(go.Scatter(x=monthly["month"], y=monthly["revenue"], mode="lines+markers", name="Revenue", line={"color": "#315eea", "width": 3}))
            figure.add_trace(go.Scatter(x=monthly["month"], y=monthly["spend"], mode="lines+markers", name="Spend", line={"color": "#f08c46", "width": 3}))
            figure.update_layout(template="plotly_white", height=330, margin={"l": 8, "r": 8, "t": 15, "b": 8}, legend={"orientation": "h", "y": 1.15}, yaxis_title="Amount (INR)")
            st.plotly_chart(figure, width="stretch")
        else:
            st.info("No activity in this date range.")
    with channels_col:
        st.subheader("Revenue by channel")
        nonzero = channels[channels["revenue"] > 0]
        if not nonzero.empty:
            figure = px.pie(nonzero, values="revenue", names="channel_name", hole=0.66, color_discrete_sequence=px.colors.qualitative.Safe)
            figure.update_layout(template="plotly_white", height=330, margin={"l": 0, "r": 0, "t": 10, "b": 4}, legend={"orientation": "h", "y": -0.1})
            st.plotly_chart(figure, width="stretch")
        else:
            st.info("No conversion revenue in this selection.")
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Campaigns by revenue")
        top = performance.nlargest(8, "revenue")
        if not top.empty:
            figure = px.bar(top.sort_values("revenue"), x="revenue", y="campaign_name", orientation="h", color="roas", color_continuous_scale="Blues", labels={"revenue": "Revenue (INR)", "campaign_name": "", "roas": "ROAS"})
            figure.update_layout(template="plotly_white", height=350, margin={"l": 8, "r": 8, "t": 10, "b": 5}, coloraxis_showscale=False)
            st.plotly_chart(figure, width="stretch")
    with right:
        st.subheader("Quick read")
        if not performance.empty:
            best = performance.loc[performance["roas"].idxmax()]
            costly = performance[performance["conversions"] > 0].nlargest(1, "cpa")
            st.markdown(
                f"""
                <div class="card"><span class="pill">TOP ROAS</span><h3>{best['campaign_name']}</h3>
                <p class="muted">{best['roas']:.2f}x return on ad spend</p></div>
                """,
                unsafe_allow_html=True,
            )
            if not costly.empty:
                row = costly.iloc[0]
                st.markdown(
                    f'<div class="card"><span class="pill">CPA WATCH</span><h3>{row["campaign_name"]}</h3><p class="muted">{money(row["cpa"])} per conversion</p></div>',
                    unsafe_allow_html=True,
                )
        st.caption("ROAS is revenue divided by recorded marketing spend. It is not net profit.")


def render_findings() -> None:
    title_block(
        "Data analyst findings",
        "A concise, metric-backed readout of the selected campaign and channel portfolio.",
    )
    funnel = funnel_totals(spend_df, leads_df, conversions_df)
    findings = build_analyst_findings(performance, channels, funnel)
    for finding in findings:
        with st.container(border=True):
            st.markdown(f"**{finding['priority']}**")
            st.subheader(finding["title"])
            st.write(f"**Evidence:** {finding['evidence']}")
            st.write(f"**Suggested next step:** {finding['action']}")

    st.subheader("Comparison context")
    left, right = st.columns(2)
    with left:
        st.markdown("**Channel scorecard**")
        show_table(
            channels.sort_values("roas", ascending=False),
            ["channel_name", "spend", "revenue", "conversions", "cpa", "roas"],
            {"spend": "₹{:,.0f}", "revenue": "₹{:,.0f}", "cpa": "₹{:,.0f}", "roas": "{:.2f}x"},
        )
    with right:
        st.markdown("**Funnel stage volumes**")
        st.dataframe(funnel, width="stretch", hide_index=True)
    st.caption(
        "These are descriptive findings from the selected data, not proof of causal impact. "
        "Check sample size, attribution, and tracking quality before acting."
    )
    findings_csv = pd.DataFrame(findings).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Download findings (CSV)",
        findings_csv,
        file_name="data-analyst-findings.csv",
        mime="text/csv",
        width="stretch",
    )


def render_forecast() -> None:
    title_block(
        "Forecast & trends",
        "An exploratory linear trend baseline for monthly spend or attributed revenue.",
    )
    metric_label = st.selectbox("Metric to forecast", ["Revenue", "Marketing spend"])
    horizon = st.slider("Forecast horizon (months)", min_value=1, max_value=6, value=3)
    metric_column = "revenue" if metric_label == "Revenue" else "spend"
    monthly = monthly_performance()
    if len(monthly) < 4:
        st.info("Select a date range containing at least four complete months to create a forecast.")
        return

    try:
        forecast, backtest = forecast_monthly_trend(monthly, metric_column, horizon)
    except ValueError as error:
        st.error(f"Forecast unavailable: {error}")
        return

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=monthly["month"],
            y=monthly[metric_column],
            mode="lines+markers",
            name="Historical",
            line={"color": "#315eea", "width": 3},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=forecast["month"],
            y=forecast["lower"],
            mode="lines",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=forecast["month"],
            y=forecast["upper"],
            mode="lines",
            line={"width": 0},
            fill="tonexty",
            fillcolor="rgba(49, 94, 234, 0.14)",
            name="Approx. trend range",
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=forecast["month"],
            y=forecast["forecast"],
            mode="lines+markers",
            name="Trend forecast",
            line={"color": "#f08c46", "width": 3, "dash": "dash"},
        )
    )
    figure.update_layout(
        template="plotly_white",
        height=420,
        margin={"l": 8, "r": 8, "t": 15, "b": 8},
        yaxis_title=f"{metric_label} (INR)",
    )
    st.plotly_chart(figure, width="stretch")
    show_table(
        forecast,
        ["month", "forecast", "lower", "upper"],
        {"forecast": "₹{:,.0f}", "lower": "₹{:,.0f}", "upper": "₹{:,.0f}"},
    )
    if backtest:
        left, right = st.columns(2)
        left.metric("2-month holdout MAE", money(backtest["mae"]))
        right.metric("2-month holdout MAPE", f"{backtest['mape']:.1f}%")
        st.caption("MAPE excludes months with zero actual values. Holdout errors are descriptive and may not predict future accuracy.")
    st.warning(
        "This is a simple linear trend baseline, not a seasonality-aware or causal forecast. "
        "The shaded range is an approximate residual band, not a formal confidence interval. "
        "Use it for exploration, not as a budget commitment."
    )


def render_campaigns() -> None:
    title_block("Campaign analytics", "Compare campaign efficiency, delivery, acquisition cost, and budget pacing.")
    show_kpis()
    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Campaign performance")
        show_table(
            performance.sort_values("revenue", ascending=False),
            ["campaign_name", "channel_name", "budget", "spend", "impressions", "clicks", "conversions", "revenue", "ctr", "cpc", "cpa", "roas", "budget_used"],
            {"budget": "₹{:,.0f}", "spend": "₹{:,.0f}", "revenue": "₹{:,.0f}", "ctr": "{:.2f}%", "cpc": "₹{:,.2f}", "cpa": "₹{:,.0f}", "roas": "{:.2f}x", "budget_used": "{:.1f}%"},
        )
    with right:
        st.subheader("Spend versus revenue")
        plot_data = performance[performance["spend"] + performance["revenue"] > 0]
        if not plot_data.empty:
            chart_data = plot_data.melt(id_vars="campaign_name", value_vars=["spend", "revenue"], var_name="measure", value_name="amount")
            figure = px.bar(chart_data, x="campaign_name", y="amount", color="measure", barmode="group", color_discrete_map={"spend": "#f08c46", "revenue": "#315eea"})
            figure.update_layout(template="plotly_white", height=430, xaxis_tickangle=-45, margin={"l": 8, "r": 8, "t": 10, "b": 8}, yaxis_title="Amount (INR)")
            st.plotly_chart(figure, width="stretch")
    st.caption("CTR = clicks / impressions; CPC = spend / clicks; CPA = spend / conversions; conversion rate = conversions / clicks.")


def render_channels() -> None:
    title_block("Channel performance", "See where acquisition budget is producing the strongest return.")
    show_kpis()
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Channel scorecard")
        show_table(
            channels.sort_values("revenue", ascending=False),
            ["channel_name", "spend", "revenue", "conversions", "ctr", "cpc", "cpa", "roas"],
            {"spend": "₹{:,.0f}", "revenue": "₹{:,.0f}", "ctr": "{:.2f}%", "cpc": "₹{:,.2f}", "cpa": "₹{:,.0f}", "roas": "{:.2f}x"},
        )
    with right:
        st.subheader("Spend and revenue")
        if not channels.empty:
            long_data = channels.melt(id_vars="channel_name", value_vars=["spend", "revenue"], var_name="measure", value_name="amount")
            figure = px.bar(long_data, x="channel_name", y="amount", color="measure", barmode="group", color_discrete_map={"spend": "#f08c46", "revenue": "#315eea"})
            figure.update_layout(template="plotly_white", height=390, xaxis_tickangle=-35, margin={"l": 8, "r": 8, "t": 10, "b": 8}, yaxis_title="Amount (INR)")
            st.plotly_chart(figure, width="stretch")
    if not channels.empty:
        best = channels.loc[channels["roas"].idxmax()]
        st.info(f"Highest observed ROAS: **{best['channel_name']}** at **{best['roas']:.2f}x**. Validate marginal returns before shifting budget.")


def render_customers() -> None:
    title_block("Customer insights", "Understand who converts, who returns, and how acquisition varies by segment.")
    customer_counts = customer_conversions_df.groupby("customer_id")["conversion_id"].count()
    unique_customers = int(customer_counts.size)
    repeat_customers = int((customer_counts > 1).sum())
    repeat_rate = safe_ratio(repeat_customers, unique_customers) * 100
    average_value = safe_ratio(float(customer_conversions_df["revenue"].sum()), unique_customers)
    high_value = int((customer_conversions_df.groupby("customer_id")["revenue"].sum() >= 25_000).sum()) if unique_customers else 0
    columns = st.columns(4)
    columns[0].metric("Converting customers", f"{unique_customers:,}")
    columns[1].metric("Repeat customer rate", f"{repeat_rate:.1f}%")
    columns[2].metric("Revenue per customer", money(average_value))
    columns[3].metric("High-value customers", f"{high_value:,}")
    left, right = st.columns(2)
    with left:
        st.subheader("Customers by segment")
        segment_data = customer_conversions_df.groupby("segment", as_index=False).agg(customers=("customer_id", "nunique"), revenue=("revenue", "sum"))
        if not segment_data.empty:
            figure = px.bar(segment_data.sort_values("customers"), x="customers", y="segment", orientation="h", color="revenue", color_continuous_scale="Blues")
            figure.update_layout(template="plotly_white", height=330, margin={"l": 8, "r": 8, "t": 10, "b": 8})
            st.plotly_chart(figure, width="stretch")
        else:
            st.info("No customers converted in this selection.")
    with right:
        st.subheader("Revenue by region")
        region_data = customer_conversions_df.groupby("region", as_index=False).agg(customers=("customer_id", "nunique"), revenue=("revenue", "sum"))
        if not region_data.empty:
            figure = px.bar(region_data.sort_values("revenue"), x="revenue", y="region", orientation="h", color="customers", color_continuous_scale="Teal")
            figure.update_layout(template="plotly_white", height=330, margin={"l": 8, "r": 8, "t": 10, "b": 8}, xaxis_title="Revenue (INR)")
            st.plotly_chart(figure, width="stretch")
        else:
            st.info("No regional revenue in this selection.")
    st.caption("High value is a demo definition: at least INR 25,000 in selected-period conversion revenue. This is not a predictive lifetime-value model.")


def render_funnel() -> None:
    title_block("Conversion funnel", "Find the stage with the largest volume drop-off in the selected campaign mix.")
    funnel = funnel_totals(spend_df, leads_df, conversions_df)
    columns = st.columns(4)
    for column, row in zip(columns, funnel.itertuples(index=False)):
        column.metric(row.stage, f"{row.count:,}")
    left, right = st.columns([1.3, 1])
    with left:
        figure = px.funnel(funnel, x="count", y="stage", color="stage", color_discrete_sequence=["#315eea", "#5478ef", "#8ba0f4", "#f08c46"])
        figure.update_layout(template="plotly_white", height=390, margin={"l": 8, "r": 8, "t": 15, "b": 8}, showlegend=False)
        st.plotly_chart(figure, width="stretch")
    with right:
        st.subheader("Stage conversion")
        rows = []
        prior = None
        for row in funnel.itertuples(index=False):
            rows.append({"Stage": row.stage, "Volume": row.count, "Conversion from prior": "—" if prior is None else f"{safe_ratio(row.count, prior) * 100:.1f}%", "Drop-off from prior": "—" if prior is None else f"{(1 - safe_ratio(row.count, prior)) * 100:.1f}%"})
            prior = row.count
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.caption("The funnel is built from activity aggregates. Lead records may include repeated customers.")


def render_roi() -> None:
    title_block("Revenue & ROI", "Measure marketing-attributed revenue and spend without confusing ROAS with profit.")
    show_kpis()
    revenue = float(conversions_df["revenue"].sum())
    spend = float(spend_df["spend"].sum())
    marketing_return = (revenue - spend) / spend * 100 if spend else 0
    columns = st.columns(3)
    columns[0].metric("Marketing return", f"{marketing_return:.1f}%")
    columns[1].metric("Cost per acquisition", money(safe_ratio(spend, conversions_df["conversion_id"].nunique())))
    columns[2].metric("Revenue per conversion", money(safe_ratio(revenue, conversions_df["conversion_id"].nunique())))
    monthly = monthly_performance()
    if not monthly.empty:
        monthly["roas"] = monthly.apply(lambda row: safe_ratio(row["revenue"], row["spend"]), axis=1)
        figure = go.Figure()
        figure.add_trace(go.Bar(x=monthly["month"], y=monthly["spend"], name="Spend", marker_color="#f08c46"))
        figure.add_trace(go.Bar(x=monthly["month"], y=monthly["revenue"], name="Revenue", marker_color="#315eea"))
        figure.update_layout(template="plotly_white", barmode="group", height=370, margin={"l": 8, "r": 8, "t": 15, "b": 8}, yaxis_title="Amount (INR)")
        st.plotly_chart(figure, width="stretch")
        show_table(monthly, ["month", "spend", "revenue", "roas"], {"spend": "₹{:,.0f}", "revenue": "₹{:,.0f}", "roas": "{:.2f}x"})
    st.warning("Marketing return and ROAS use attributed revenue and ad spend only. Product costs, overhead, and incrementality are not included, so these are not net profit or causal lift.")


def recommendations() -> list[dict[str, str]]:
    return build_recommendations(performance, channels, conversions_df)


def render_growth() -> None:
    title_block("Growth opportunities", "Evidence-led signals generated from the currently selected portfolio.")
    items = recommendations()
    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Prioritized opportunities")
        for item in items:
            st.markdown(
                f"""
                <div class="card">
                  <span class="pill">{item['priority']} PRIORITY · {item['category'].upper()}</span>
                  <h3>{item['problem']}</h3>
                  <p><b>Evidence:</b> {item['evidence']}</p>
                  <p><b>Action:</b> {item['action']}</p>
                  <p class="muted"><b>Expected benefit:</b> {item['benefit']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with right:
        st.subheader("Budget allocation lens")
        if not channels.empty:
            scatter = px.scatter(channels, x="spend", y="roas", size="conversions", color="channel_name", hover_name="channel_name", labels={"spend": "Spend (INR)", "roas": "ROAS"})
            scatter.update_layout(template="plotly_white", height=440, showlegend=False, margin={"l": 8, "r": 8, "t": 10, "b": 8})
            st.plotly_chart(scatter, width="stretch")
        st.caption("Observational comparisons are directional. Test budget changes and monitor marginal CPA.")


def render_recommendations() -> None:
    title_block("Recommendations & action centre", "Assign an owner decision and track the follow-through for each evidence-backed action.")
    items = recommendations()
    actions = recommendation_actions(database)
    for item in items:
        with st.container(border=True):
            left, right = st.columns([2, 1])
            with left:
                st.markdown(f"**{item['category']}** · `{item['priority']} priority`")
                st.subheader(item["problem"])
                st.write(f"**Evidence:** {item['evidence']}")
                st.write(f"**Suggested action:** {item['action']}")
                st.caption(f"Expected benefit: {item['benefit']}")
            with right:
                saved = actions.get(item["key"], {"status": "Pending", "decision": ""})
                status = st.selectbox("Status", ["Pending", "In Progress", "Completed"], index=["Pending", "In Progress", "Completed"].index(saved["status"]), key=f"status-{item['key']}")
                decision = st.text_area("Manager decision / note", value=saved["decision"], key=f"decision-{item['key']}", height=90)
                if st.button("Save action", key=f"save-{item['key']}"):
                    save_recommendation_action(database, item["key"], status, decision)
                    st.success("Action saved.")
    st.caption("Action status is stored in the local SQLite database. On Streamlit Community Cloud, the filesystem may reset on a new deployment or restart.")


def make_pdf(performance_data: pd.DataFrame, channel_data: pd.DataFrame) -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], alignment=TA_LEFT, textColor=colors.HexColor("#14213d"), spaceAfter=5))
    story = [
        Paragraph("Marketing Performance Report", styles["ReportTitle"]),
        Paragraph(f"Selected period: {start_date.date().isoformat()} to {end_date.date().isoformat()}", styles["Normal"]),
        Spacer(1, 8 * mm),
    ]
    total_revenue = float(conversions_df["revenue"].sum())
    total_spend = float(spend_df["spend"].sum())
    kpi_data = [
        ["Revenue (INR)", "Spend (INR)", "Conversions", "ROAS"],
        [f"{total_revenue:,.0f}", f"{total_spend:,.0f}", f"{conversions_df['conversion_id'].nunique():,}", f"{safe_ratio(total_revenue, total_spend):.2f}x"],
    ]
    story.extend([Table(kpi_data, colWidths=[43 * mm] * 4), Spacer(1, 8 * mm), Paragraph("Campaign performance", styles["Heading2"])])
    campaign_rows = [["Campaign", "Channel", "Spend", "Revenue", "Conversions", "ROAS"]]
    for row in performance_data.nlargest(15, "revenue").itertuples():
        campaign_rows.append([str(row.campaign_name)[:30], str(row.channel_name), f"{row.spend:,.0f}", f"{row.revenue:,.0f}", f"{row.conversions:.0f}", f"{row.roas:.2f}x"])
    story.append(Table(campaign_rows, repeatRows=1, colWidths=[45 * mm, 30 * mm, 25 * mm, 25 * mm, 24 * mm, 18 * mm]))
    story.extend([Spacer(1, 8 * mm), Paragraph("Channel performance", styles["Heading2"])])
    channel_rows = [["Channel", "Spend", "Revenue", "Conversions", "ROAS"]]
    for row in channel_data.sort_values("revenue", ascending=False).itertuples():
        channel_rows.append([str(row.channel_name), f"{row.spend:,.0f}", f"{row.revenue:,.0f}", f"{row.conversions:.0f}", f"{row.roas:.2f}x"])
    story.append(Table(channel_rows, repeatRows=1, colWidths=[52 * mm, 32 * mm, 32 * mm, 32 * mm, 20 * mm]))
    source_label = "Uploaded data" if data_is_uploaded else "Synthetic sample data"
    story.extend([Spacer(1, 5 * mm), Paragraph(f"{source_label}. ROAS is attributed revenue divided by marketing spend and is not net profit.", styles["Italic"])])
    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0ff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#14213d")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce2ed")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f8fb")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )
    for element in story:
        if isinstance(element, Table):
            element.setStyle(table_style)
    document.build(story)
    return output.getvalue()


def render_reports() -> None:
    title_block("Reports & export", "Download filtered campaign and channel scorecards for sharing and follow-up.")
    st.info(f"Report period: {start_date.date().isoformat()} – {end_date.date().isoformat()}. All figures reflect the global filters in the sidebar.")
    report_campaigns = performance.sort_values("revenue", ascending=False)
    report_channels = channels.sort_values("revenue", ascending=False)
    left, right = st.columns(2)
    with left:
        st.download_button(
            "Download campaign report (CSV)",
            report_campaigns.to_csv(index=False).encode("utf-8-sig"),
            file_name="campaign-performance.csv",
            mime="text/csv",
            width="stretch",
        )
    with right:
        st.download_button(
            "Download channel report (CSV)",
            report_channels.to_csv(index=False).encode("utf-8-sig"),
            file_name="channel-performance.csv",
            mime="text/csv",
            width="stretch",
        )
    st.download_button(
        "Download portfolio report (PDF)",
        make_pdf(report_campaigns, report_channels),
        file_name="marketing-performance-report.pdf",
        mime="application/pdf",
        width="stretch",
    )
    st.subheader("Campaign report preview")
    show_table(report_campaigns, ["campaign_name", "channel_name", "spend", "revenue", "conversions", "cpa", "roas"], {"spend": "₹{:,.0f}", "revenue": "₹{:,.0f}", "cpa": "₹{:,.0f}", "roas": "{:.2f}x"})


PAGES = {
    "Executive Overview": render_overview,
    "Data Analyst Findings": render_findings,
    "Campaign Analytics": render_campaigns,
    "Channel Performance": render_channels,
    "Customer Insights": render_customers,
    "Conversion Funnel": render_funnel,
    "Revenue & ROI": render_roi,
    "Forecast & Trends": render_forecast,
    "Growth Opportunities": render_growth,
    "Recommendations": render_recommendations,
    "Reports & Export": render_reports,
}

PAGES[page]()
