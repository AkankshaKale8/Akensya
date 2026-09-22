from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


DATASET_SPECS = {
    "customers": {
        "required": {"customer_id"},
        "aliases": {
            "id": "customer_id",
            "customer": "customer_id",
            "customerid": "customer_id",
            "customer_id": "customer_id",
            "clv": "lifetime_value",
            "ltv": "lifetime_value",
            "lifetimevalue": "lifetime_value",
            "lifetime_value": "lifetime_value",
        },
    },
    "campaigns": {
        "required": {"campaign_id"},
        "aliases": {
            "id": "campaign_id",
            "campaign": "campaign_id",
            "campaignid": "campaign_id",
            "campaign_id": "campaign_id",
        },
    },
    "interactions": {
        "required": {"customer_id"},
        "aliases": {
            "customer": "customer_id",
            "customerid": "customer_id",
            "customer_id": "customer_id",
        },
    },
    "sustainability": {
        "required": set(),
        "aliases": {},
    },
    "transactions": {
        "required": {"customer_id"},
        "aliases": {
            "customer": "customer_id",
            "customerid": "customer_id",
            "customer_id": "customer_id",
            "amount": "amount",
            "revenue": "amount",
            "sales": "amount",
            "value": "amount",
        },
    },
}


def _clean_column_name(value: str) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace("&", "and")
        .replace("-", "_")
        .replace(" ", "_")
    )


def normalize_data(entity: str, df: pd.DataFrame) -> pd.DataFrame:
    """Normalize uploaded data without assuming a specific vendor schema."""
    if entity not in DATASET_SPECS:
        raise ValueError(f"Unsupported dataset: {entity}")

    out = df.copy()
    out.columns = [_clean_column_name(c) for c in out.columns]

    aliases = DATASET_SPECS[entity]["aliases"]
    rename = {}
    for col in out.columns:
        rename[col] = aliases.get(col, col)
    out = out.rename(columns=rename)

    # Common date fields.
    for col in list(out.columns):
        if col in {"date", "timestamp", "signup_date", "last_purchase_date"} or "date" in col:
            converted = pd.to_datetime(out[col], errors="coerce")
            if converted.notna().any():
                out[col] = converted

    # Common numeric fields.
    numeric_candidates = {
        "amount", "spend", "revenue", "sales", "impressions", "clicks",
        "conversions", "lifetime_value", "clv", "orders", "quantity",
        "estimated_emissions", "emissions", "carbon_kg",
    }
    for col in out.columns:
        if col in numeric_candidates:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    return out


def validate_dataset(entity: str, df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate a dataset before it can affect analytics."""
    if entity not in DATASET_SPECS:
        return False, [f"Unsupported dataset type: {entity}"]

    if df is None or df.empty:
        return False, ["The uploaded file contains no records."]

    normalized = normalize_data(entity, df)
    required = DATASET_SPECS[entity]["required"]
    missing = sorted(required - set(normalized.columns))

    errors = []
    if missing:
        errors.append(
            f"Missing required columns: {', '.join(missing)}"
        )

    if entity == "transactions" and "amount" not in normalized.columns:
        errors.append("Transactions require an amount/revenue/sales column.")

    if entity == "campaigns":
        if not any(c in normalized.columns for c in ["spend", "revenue", "impressions", "clicks"]):
            errors.append("Campaigns should contain at least one performance field such as spend, revenue, impressions or clicks.")

    return len(errors) == 0, errors


def process_upload(entity: str, uploaded_file) -> pd.DataFrame:
    raw = pd.read_csv(uploaded_file)
    normalized = normalize_data(entity, raw)
    valid, errors = validate_dataset(entity, normalized)
    if not valid:
        raise ValueError(" ".join(errors))
    return normalized


def data_quality(df: pd.DataFrame) -> Dict:
    records = len(df)
    cells = max(df.shape[0] * df.shape[1], 1)
    missing_pct = float(df.isna().sum().sum() / cells * 100)
    duplicate_pct = float(df.duplicated().sum() / max(records, 1) * 100)
    score = max(0.0, min(100.0, round(100 - missing_pct * 0.7 - duplicate_pct * 0.3, 1)))
    return {
        "score": score,
        "records": records,
        "missing_pct": missing_pct,
        "duplicate_pct": duplicate_pct,
    }


def load_demo_data(data_dir) -> Dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    result = {}
    files = {
        "customers": ("customers.csv", ["signup_date"]),
        "campaigns": ("campaigns.csv", ["date"]),
        "interactions": ("interactions.csv", ["timestamp"]),
        "sustainability": ("sustainability.csv", ["date"]),
        "transactions": ("transactions.csv", ["date"]),
    }
    for entity, (filename, _) in files.items():
        path = data_dir / filename
        if path.exists():
            df = pd.read_csv(path)
            result[entity] = normalize_data(entity, df)
    return result


def dataframe_to_records(df: pd.DataFrame) -> list:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return out.where(pd.notna(out), None).to_dict(orient="records")


def records_to_dataframe(records: list) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)
