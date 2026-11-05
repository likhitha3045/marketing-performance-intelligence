from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "dataset"
SEED = 20251105
DAYS = 210

CHANNELS = [
    "Google Ads",
    "Facebook Ads",
    "Instagram",
    "Email Marketing",
    "Organic Search",
    "Referral Marketing",
]
REGIONS = ["North", "South", "East", "West", "Central", "International"]
SEGMENTS = ["New", "Returning", "High Value", "At Risk"]
PRODUCTS = [
    ("Analytics Starter", "Software"),
    ("Analytics Pro", "Software"),
    ("Growth Toolkit", "Services"),
    ("Marketing Audit", "Services"),
    ("Data Workshop", "Education"),
    ("Campaign Planner", "Software"),
    ("Customer Insights", "Software"),
    ("Strategy Session", "Services"),
    ("Reporting Pack", "Software"),
    ("Attribution Review", "Services"),
    ("Automation Suite", "Software"),
    ("Optimization Course", "Education"),
]


def write_csv(name: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write an empty dataset: {name}")
    path = DATA_DIR / name
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def generate() -> dict[str, int]:
    random.seed(SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    start = date(2025, 1, 1)
    end = start + timedelta(days=DAYS - 1)

    channel_rows = [
        {"channel_id": index, "channel_name": name}
        for index, name in enumerate(CHANNELS, start=1)
    ]
    campaign_rows = []
    campaign_performance: dict[int, tuple[float, float, float]] = {}
    campaign_types = ["Awareness", "Acquisition", "Retargeting", "Retention"]
    for campaign_id in range(1, 25):
        channel_id = (campaign_id - 1) % len(CHANNELS) + 1
        campaign_name = f"{CHANNELS[channel_id - 1]} - Campaign {campaign_id:02d}"
        budget = round(random.uniform(320_000, 780_000), 2)
        campaign_rows.append(
            {
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "campaign_type": campaign_types[(campaign_id - 1) % len(campaign_types)],
                "channel_id": channel_id,
                "budget": budget,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "status": "Completed",
            }
        )
        campaign_performance[campaign_id] = (
            random.uniform(0.75, 1.25),
            random.uniform(0.012, 0.045),
            random.uniform(0.14, 0.34),
        )

    customer_rows = []
    for customer_id in range(1, 751):
        signup_date = start - timedelta(days=random.randint(0, 365))
        customer_rows.append(
            {
                "customer_id": customer_id,
                "region": random.choice(REGIONS),
                "segment": random.choices(SEGMENTS, weights=[48, 28, 12, 12])[0],
                "signup_date": signup_date.isoformat(),
            }
        )

    spend_rows = []
    leads = []
    lead_id = 1
    for campaign in campaign_rows:
        campaign_id = int(campaign["campaign_id"])
        spend_multiplier, click_rate, conversion_rate = campaign_performance[campaign_id]
        for day_index in range(DAYS):
            activity_date = start + timedelta(days=day_index)
            impressions = max(100, int(random.randint(500, 1800) * spend_multiplier))
            clicks = min(impressions, int(impressions * click_rate))
            spend = round(
                (float(campaign["budget"]) / DAYS)
                * random.uniform(0.82, 1.14)
                * spend_multiplier,
                2,
            )
            spend_rows.append(
                {
                    "campaign_id": campaign_id,
                    "activity_date": activity_date.isoformat(),
                    "spend": spend,
                    "impressions": impressions,
                    "clicks": clicks,
                }
            )
            daily_leads = int(clicks * random.uniform(0.04, 0.09))
            for _ in range(daily_leads):
                leads.append(
                    {
                        "lead_id": lead_id,
                        "customer_id": random.randint(1, len(customer_rows)),
                        "campaign_id": campaign_id,
                        "lead_date": activity_date.isoformat(),
                        "status": "Converted" if random.random() < conversion_rate else "Open",
                    }
                )
                lead_id += 1

    conversion_rows = []
    transaction_rows = []
    for lead in leads:
        if lead["status"] != "Converted":
            continue
        conversion_id = len(conversion_rows) + 1
        revenue = round(random.uniform(2_500, 18_000), 2)
        conversion_rows.append(
            {
                "conversion_id": conversion_id,
                "lead_id": lead["lead_id"],
                "customer_id": lead["customer_id"],
                "campaign_id": lead["campaign_id"],
                "conversion_date": lead["lead_date"],
                "revenue": revenue,
            }
        )
        product_id = random.randint(1, len(PRODUCTS))
        transaction_rows.append(
            {
                "transaction_id": conversion_id,
                "conversion_id": conversion_id,
                "customer_id": lead["customer_id"],
                "product_id": product_id,
                "transaction_date": lead["lead_date"],
                "amount": revenue,
            }
        )

    product_rows = [
        {"product_id": index, "product_name": name, "category": category}
        for index, (name, category) in enumerate(PRODUCTS, start=1)
    ]
    write_csv("channels.csv", channel_rows)
    write_csv("campaigns.csv", campaign_rows)
    write_csv("customers.csv", customer_rows)
    write_csv("marketing_spend.csv", spend_rows)
    write_csv("leads.csv", leads)
    write_csv("conversions.csv", conversion_rows)
    write_csv("products.csv", product_rows)
    write_csv("transactions.csv", transaction_rows)
    return {
        "channels": len(channel_rows),
        "campaigns": len(campaign_rows),
        "customers": len(customer_rows),
        "marketing activity records": len(spend_rows),
        "leads": len(leads),
        "conversions": len(conversion_rows),
        "products": len(product_rows),
        "transactions": len(transaction_rows),
    }


if __name__ == "__main__":
    counts = generate()
    for table, count in counts.items():
        print(f"{table}: {count:,}")
    print(f"Synthetic CSVs written to {DATA_DIR}")
