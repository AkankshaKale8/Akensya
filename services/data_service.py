
from pathlib import Path
import pandas as pd
import numpy as np

def load_demo_data(data_dir):
    return {
        "customers": pd.read_csv(Path(data_dir)/"customers.csv", parse_dates=["signup_date"]),
        "campaigns": pd.read_csv(Path(data_dir)/"campaigns.csv", parse_dates=["date"]),
        "interactions": pd.read_csv(Path(data_dir)/"interactions.csv", parse_dates=["timestamp"]),
        "sustainability": pd.read_csv(Path(data_dir)/"sustainability.csv", parse_dates=["date"]),
        "transactions": pd.read_csv(Path(data_dir)/"transactions.csv", parse_dates=["date"]),
    }

def process_upload(entity, uploaded_file):
    df = pd.read_csv(uploaded_file)
    return normalize_data(entity, df)

def normalize_data(entity, df):
    df = df.copy()
    date_cols = [c for c in df.columns if c in {"date","timestamp","signup_date"} or "date" in c]
    for c in date_cols:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
    return df

def data_quality(df):
    records = len(df)
    cells = max(df.shape[0] * df.shape[1], 1)
    missing_pct = df.isna().sum().sum() / cells * 100
    duplicate_pct = df.duplicated().sum() / max(records,1) * 100
    score = max(0, min(100, round(100 - missing_pct*.7 - duplicate_pct*.3, 1)))
    return {"score":score,"records":records,"missing_pct":missing_pct,"duplicate_pct":duplicate_pct}
