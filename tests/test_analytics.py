from __future__ import annotations

import unittest

import pandas as pd

from marketing_intelligence.analytics import (
    build_analyst_findings,
    build_recommendations,
    campaign_performance,
    channel_performance,
    forecast_monthly_trend,
    funnel_totals,
    load_uploaded_frames,
)
from marketing_intelligence.data_pipeline import DATA_DIR, TABLE_FILES


class AnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.campaigns = pd.DataFrame(
            [
                {"campaign_id": 1, "campaign_name": "A", "channel_name": "Search", "budget": 100.0},
                {"campaign_id": 2, "campaign_name": "B", "channel_name": "Social", "budget": 100.0},
            ]
        )
        self.spend = pd.DataFrame(
            [
                {"campaign_id": 1, "spend": 20.0, "impressions": 1000, "clicks": 100},
                {"campaign_id": 1, "spend": 30.0, "impressions": 2000, "clicks": 100},
                {"campaign_id": 2, "spend": 0.0, "impressions": 0, "clicks": 0},
            ]
        )
        self.conversions = pd.DataFrame(
            [
                {"conversion_id": 1, "campaign_id": 1, "channel_name": "Search", "customer_id": 10, "revenue": 100.0},
                {"conversion_id": 2, "campaign_id": 1, "channel_name": "Search", "customer_id": 11, "revenue": 100.0},
            ]
        )

    def test_campaign_facts_are_aggregated_without_fanout(self) -> None:
        result = campaign_performance(self.spend, self.conversions, self.campaigns).set_index("campaign_id")
        self.assertEqual(result.loc[1, "spend"], 50.0)
        self.assertEqual(result.loc[1, "revenue"], 200.0)
        self.assertEqual(result.loc[1, "conversions"], 2)
        self.assertEqual(result.loc[1, "roas"], 4.0)

    def test_zero_denominators_return_zero(self) -> None:
        result = campaign_performance(self.spend, self.conversions, self.campaigns).set_index("campaign_id")
        self.assertEqual(result.loc[2, "ctr"], 0.0)
        self.assertEqual(result.loc[2, "cpc"], 0.0)
        self.assertEqual(result.loc[2, "cpa"], 0.0)
        self.assertEqual(result.loc[2, "roas"], 0.0)

    def test_channel_performance_uses_campaign_channel_relation(self) -> None:
        result = channel_performance(self.spend, self.conversions, self.campaigns).set_index("channel_name")
        self.assertEqual(result.loc["Search", "spend"], 50.0)
        self.assertEqual(result.loc["Search", "revenue"], 200.0)

    def test_funnel_counts_distinct_fact_ids(self) -> None:
        leads = pd.DataFrame({"lead_id": [1, 2, 2]})
        funnel = funnel_totals(self.spend, leads, self.conversions)
        self.assertEqual(funnel["count"].tolist(), [3000, 200, 2, 2])

    def test_recommendations_include_metric_evidence(self) -> None:
        performance = campaign_performance(self.spend, self.conversions, self.campaigns)
        channel = channel_performance(self.spend, self.conversions, self.campaigns)
        items = build_recommendations(performance, channel, self.conversions)
        self.assertTrue(items)
        self.assertTrue(all(item["evidence"] and item["action"] for item in items))

    def test_findings_include_evidence_for_selected_metrics(self) -> None:
        performance = campaign_performance(self.spend, self.conversions, self.campaigns)
        channel = channel_performance(self.spend, self.conversions, self.campaigns)
        funnel = funnel_totals(
            self.spend,
            pd.DataFrame({"lead_id": [1, 2, 3]}),
            self.conversions,
        )
        findings = build_analyst_findings(performance, channel, funnel)
        self.assertTrue(findings)
        self.assertTrue(all(item["evidence"] and item["action"] for item in findings))

    def test_linear_forecast_projects_months_and_backtests(self) -> None:
        monthly = pd.DataFrame(
            {
                "month": pd.date_range("2025-01-01", periods=8, freq="MS"),
                "revenue": [100, 120, 140, 160, 180, 200, 220, 240],
            }
        )
        forecast, backtest = forecast_monthly_trend(monthly, "revenue", horizon=3)
        self.assertEqual(len(forecast), 3)
        self.assertEqual(forecast["month"].dt.month.tolist(), [9, 10, 11])
        self.assertTrue((forecast["forecast"] > 0).all())
        self.assertIsNotNone(backtest)
        self.assertAlmostEqual(backtest["mae"], 0)

    def test_forecast_requires_sufficient_months(self) -> None:
        monthly = pd.DataFrame(
            {"month": pd.date_range("2025-01-01", periods=3, freq="MS"), "revenue": [10, 20, 30]}
        )
        with self.assertRaisesRegex(ValueError, "four complete months"):
            forecast_monthly_trend(monthly, "revenue")

    def test_uploaded_csvs_are_validated_and_loaded(self) -> None:
        uploads = {
            filename: (DATA_DIR / filename).read_bytes()
            for filename in TABLE_FILES.values()
        }
        frames = load_uploaded_frames(uploads)
        self.assertEqual(len(frames["campaigns"]), 24)
        self.assertEqual(len(frames["spend"]), 5_040)
        self.assertEqual(len(frames["conversions"]), 1_718)

    def test_upload_rejects_missing_csvs(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing required CSV"):
            load_uploaded_frames({})

    def test_upload_rejects_missing_required_columns(self) -> None:
        uploads = {
            filename: (DATA_DIR / filename).read_bytes()
            for filename in TABLE_FILES.values()
        }
        uploads["channels.csv"] = uploads["channels.csv"].replace(
            b"channel_name", b"channel_label", 1
        )
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            load_uploaded_frames(uploads)


if __name__ == "__main__":
    unittest.main()
