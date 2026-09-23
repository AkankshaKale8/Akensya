from pathlib import Path
from io import StringIO
import pandas as pd
import numpy as np

ENTITIES = ["customers", "campaigns", "interactions", "sustainability", "transactions"]
REQUIRED = {
    "customers": ["customer_id"],
    "campaigns": ["campaign_name", "spend", "revenue"],
    "interactions": ["customer_id", "stage"],
    "sustainability": ["channel", "estimated_emissions"],
    "transactions": ["customer_id", "amount", "date"],
}
ALIASES = {
    "customers": {"customerid":"customer_id","customer":"customer_id","customer_name":"name","clv":"lifetime_value","ltv":"lifetime_value","customer_value":"lifetime_value","acquisition":"acquisition_channel","channel":"acquisition_channel"},
    "campaigns": {"campaign":"campaign_name","campaign_id":"campaign_id","cost":"spend","budget":"spend","sales":"revenue","orders":"conversions","conversion":"conversions","views":"impressions"},
    "interactions": {"customerid":"customer_id","event_time":"timestamp","time":"timestamp","journey_stage":"stage","converted_flag":"converted"},
    "sustainability": {"emissions":"estimated_emissions","carbon":"estimated_emissions","co2":"estimated_emissions"},
    "transactions": {"customerid":"customer_id","transaction_date":"date","sales":"amount","revenue":"amount","value":"amount","qty":"quantity"},
}
DATE_HINTS = {"date", "timestamp", "signup_date", "first_purchase_date", "last_purchase_date"}


def _clean_col(c):
    return str(c).strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")


def normalize_data(entity, df):
    df = df.copy()
    df.columns = [_clean_col(c) for c in df.columns]
    for c, target in ALIASES.get(entity, {}).items():
        if c in df.columns and target not in df.columns:
            df = df.rename(columns={c: target})
    for c in list(df.columns):
        if c in DATE_HINTS or "date" in c or "time" in c:
            parsed = pd.to_datetime(df[c], errors="coerce")
            if parsed.notna().mean() >= 0.5:
                df[c] = parsed
    for c in df.columns:
        if c not in DATE_HINTS and df[c].dtype == "object":
            cleaned = df[c].astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False).str.replace("$", "", regex=False).str.strip()
            numeric = pd.to_numeric(cleaned, errors="coerce")
            if numeric.notna().mean() >= 0.85:
                df[c] = numeric
    return df


def load_demo_data(data_dir):
    data_dir = Path(data_dir)
    return {
        "customers": pd.read_csv(data_dir/"customers.csv", parse_dates=["signup_date"]),
        "campaigns": pd.read_csv(data_dir/"campaigns.csv", parse_dates=["date"]),
        "interactions": pd.read_csv(data_dir/"interactions.csv", parse_dates=["timestamp"]),
        "sustainability": pd.read_csv(data_dir/"sustainability.csv", parse_dates=["date"]),
        "transactions": pd.read_csv(data_dir/"transactions.csv", parse_dates=["date"]),
    }


def process_upload(entity, uploaded_file):
    raw = uploaded_file.getvalue()
    if len(raw) > 25 * 1024 * 1024:
        raise ValueError("For the prototype, please keep each CSV below 25 MB.")
    try:
        df = pd.read_csv(StringIO(raw.decode("utf-8-sig")))
    except UnicodeDecodeError:
        df = pd.read_csv(StringIO(raw.decode("latin-1")))
    return normalize_data(entity, df)


def data_quality(df):
    records = len(df)
    cells = max(df.shape[0] * df.shape[1], 1)
    missing_pct = float(df.isna().sum().sum() / cells * 100)
    duplicate_pct = float(df.duplicated().sum() / max(records, 1) * 100)
    score = max(0, min(100, round(100 - missing_pct * .7 - duplicate_pct * .3, 1)))
    return {"score": score, "records": records, "missing_pct": missing_pct, "duplicate_pct": duplicate_pct}


def schema_report(entity, df):
    missing = [c for c in REQUIRED.get(entity, []) if c not in df.columns]
    return {"valid": not missing, "missing_required": missing, "columns": list(df.columns)}


def empty_data():
    return {k: pd.DataFrame() for k in ENTITIES}


def data_status(data):
    return {k: (not data.get(k, pd.DataFrame()).empty) for k in ENTITIES}
