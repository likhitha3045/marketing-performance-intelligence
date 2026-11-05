from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "dataset"
SCHEMA_FILE = ROOT / "sql" / "schema.sql"

TABLE_FILES = {
    "channels": "channels.csv",
    "campaigns": "campaigns.csv",
    "customers": "customers.csv",
    "marketing_spend": "marketing_spend.csv",
    "leads": "leads.csv",
    "conversions": "conversions.csv",
    "products": "products.csv",
    "transactions": "transactions.csv",
}

REQUIRED_COLUMNS = {
    "campaigns": {"campaign_id", "campaign_name", "campaign_type", "channel_id", "budget", "start_date", "end_date", "status"},
    "channels": {"channel_id", "channel_name"},
    "customers": {"customer_id", "region", "segment", "signup_date"},
    "marketing_spend": {"campaign_id", "activity_date", "spend", "impressions", "clicks"},
    "leads": {"lead_id", "customer_id", "campaign_id", "lead_date", "status"},
    "conversions": {"conversion_id", "lead_id", "customer_id", "campaign_id", "conversion_date", "revenue"},
    "products": {"product_id", "product_name", "category"},
    "transactions": {"transaction_id", "conversion_id", "customer_id", "product_id", "transaction_date", "amount"},
}

DATE_COLUMNS = {
    "campaigns": ["start_date", "end_date"],
    "customers": ["signup_date"],
    "marketing_spend": ["activity_date"],
    "leads": ["lead_date"],
    "conversions": ["conversion_date"],
    "transactions": ["transaction_date"],
}

NUMERIC_COLUMNS = {
    "campaigns": ["budget"],
    "marketing_spend": ["spend", "impressions", "clicks"],
    "conversions": ["revenue"],
    "transactions": ["amount"],
}


def read_and_validate_csvs(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load source files, normalize text, remove duplicates, and enforce basic data rules."""
    data: dict[str, pd.DataFrame] = {}
    for table, filename in TABLE_FILES.items():
        path = data_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required source file is missing: {path}")
        frame = pd.read_csv(path)
        if frame.empty:
            raise ValueError(f"{filename} contains no data.")
        frame.columns = [column.strip().lower() for column in frame.columns]
        missing_columns = REQUIRED_COLUMNS[table] - set(frame.columns)
        if missing_columns:
            raise ValueError(f"{filename} is missing required columns: {', '.join(sorted(missing_columns))}.")
        for column in REQUIRED_COLUMNS[table]:
            if frame[column].isna().any() or (
                pd.api.types.is_object_dtype(frame[column])
                and frame[column].astype("string").str.strip().eq("").any()
            ):
                raise ValueError(f"{filename} contains missing values in {column}.")
        frame = frame.drop_duplicates().copy()

        if table == "campaigns":
            frame["campaign_name"] = (
                frame["campaign_name"].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
            )

        for column in DATE_COLUMNS.get(table, []):
            parsed = pd.to_datetime(frame[column], errors="coerce")
            if parsed.isna().any():
                raise ValueError(f"{filename} contains invalid values in {column}.")
            frame[column] = parsed.dt.strftime("%Y-%m-%d")

        for column in NUMERIC_COLUMNS.get(table, []):
            values = pd.to_numeric(frame[column], errors="coerce")
            if values.isna().any() or (values < 0).any() or not np.isfinite(values).all():
                raise ValueError(f"{filename} contains invalid or negative values in {column}.")
            frame[column] = values

        if table == "campaigns" and (
            pd.to_datetime(frame["end_date"]) < pd.to_datetime(frame["start_date"])
        ).any():
            raise ValueError(f"{filename} contains an end_date before start_date.")

        data[table] = frame

    _validate_relationships(data)
    return data


def _validate_relationships(data: dict[str, pd.DataFrame]) -> None:
    checks = [
        ("campaigns.channel_id", data["campaigns"]["channel_id"], data["channels"]["channel_id"]),
        ("marketing_spend.campaign_id", data["marketing_spend"]["campaign_id"], data["campaigns"]["campaign_id"]),
        ("leads.customer_id", data["leads"]["customer_id"], data["customers"]["customer_id"]),
        ("leads.campaign_id", data["leads"]["campaign_id"], data["campaigns"]["campaign_id"]),
        ("conversions.lead_id", data["conversions"]["lead_id"], data["leads"]["lead_id"]),
        ("conversions.customer_id", data["conversions"]["customer_id"], data["customers"]["customer_id"]),
        ("conversions.campaign_id", data["conversions"]["campaign_id"], data["campaigns"]["campaign_id"]),
        ("transactions.conversion_id", data["transactions"]["conversion_id"], data["conversions"]["conversion_id"]),
        ("transactions.customer_id", data["transactions"]["customer_id"], data["customers"]["customer_id"]),
        ("transactions.product_id", data["transactions"]["product_id"], data["products"]["product_id"]),
    ]
    for label, values, valid_values in checks:
        missing = set(values.dropna()) - set(valid_values.dropna())
        if missing:
            raise ValueError(f"{label} contains {len(missing)} unknown reference value(s).")

    conversion_leads = data["conversions"].merge(
        data["leads"][["lead_id", "customer_id", "campaign_id", "status"]],
        on="lead_id",
        how="left",
        suffixes=("_conversion", "_lead"),
    )
    mismatched_conversions = (
        (conversion_leads["customer_id_conversion"] != conversion_leads["customer_id_lead"])
        | (conversion_leads["campaign_id_conversion"] != conversion_leads["campaign_id_lead"])
        | (conversion_leads["status"] != "Converted")
    )
    if mismatched_conversions.any():
        raise ValueError("conversions.csv contains a conversion that does not match its converted lead.")

    duplicate_keys = {
        "channels": ["channel_id"],
        "campaigns": ["campaign_id"],
        "customers": ["customer_id"],
        "marketing_spend": ["campaign_id", "activity_date"],
        "leads": ["lead_id"],
        "conversions": ["conversion_id", "lead_id"],
        "products": ["product_id"],
        "transactions": ["transaction_id", "conversion_id"],
    }
    for table, columns in duplicate_keys.items():
        if data[table].duplicated(columns).any():
            raise ValueError(f"{TABLE_FILES[table]} contains duplicate key values.")


def load_database(database: Path | None = None, data_dir: Path = DATA_DIR) -> Path:
    """Create the local SQLite database from validated CSVs if it has not been seeded."""
    database = database or (data_dir / "marketing.sqlite3")
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        row = connection.execute("SELECT COUNT(*) FROM campaigns").fetchone()
        if row and row[0] > 0:
            return database

        data = read_and_validate_csvs(data_dir)
        for table, frame in data.items():
            frame.to_sql(table, connection, if_exists="append", index=False)
        connection.commit()
        _verify_database(connection)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return database


def _verify_database(connection: sqlite3.Connection) -> None:
    violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise ValueError(f"Database load created {len(violations)} foreign-key violation(s).")
    for table in TABLE_FILES:
        count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count == 0:
            raise ValueError(f"Database table {table} is empty after loading.")


def export_table_csv(connection: sqlite3.Connection, table: str) -> str:
    """Return a single validated database table as downloadable CSV text."""
    if table not in TABLE_FILES:
        raise ValueError(f"Unknown table: {table}")
    rows = connection.execute(f"SELECT * FROM {table}").fetchall()
    columns = [description[0] for description in connection.execute(f"SELECT * FROM {table} LIMIT 0").description]
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    writer.writerows(rows)
    return output.getvalue()


def get_row_counts(data_dir: Path = DATA_DIR) -> dict[str, int]:
    return {table: len(frame) for table, frame in read_and_validate_csvs(data_dir).items()}
