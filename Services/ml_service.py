from __future__ import annotations

import numpy as np
import pandas as pd


def _transactions(data):
    df = data.get("transactions")
    return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()


def revenue_forecast(data, periods=7):
    tx = _transactions(data)
    if tx.empty or "date" not in tx.columns or "amount" not in tx.columns:
        return pd.DataFrame(columns=["date", "forecast", "lower", "upper"])

    tx["date"] = pd.to_datetime(tx["date"], errors="coerce")
    tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0)
    daily = tx.dropna(subset=["date"]).groupby("date")["amount"].sum().sort_index()

    if daily.empty:
        return pd.DataFrame(columns=["date", "forecast", "lower", "upper"])

    baseline = float(daily.tail(min(7, len(daily))).mean())
    volatility = float(daily.tail(min(30, len(daily))).std()) if len(daily) > 1 else 0.0
    dates = pd.date_range(daily.index.max() + pd.Timedelta(days=1), periods=periods, freq="D")

    return pd.DataFrame({
        "date": dates,
        "forecast": baseline,
        "lower": max(0.0, baseline - volatility),
        "upper": baseline + volatility,
    })


def churn_predictions(data):
    tx = _transactions(data)
    if tx.empty or "customer_id" not in tx.columns or "date" not in tx.columns:
        return pd.DataFrame(columns=["customer_id", "days_since_purchase", "churn_probability", "risk"])

    tx["date"] = pd.to_datetime(tx["date"], errors="coerce")
    tx = tx.dropna(subset=["date"])
    if tx.empty:
        return pd.DataFrame()

    latest = tx["date"].max()
    last = tx.groupby("customer_id")["date"].max().reset_index()
    last["days_since_purchase"] = (latest - last["date"]).dt.days
    last["churn_probability"] = (last["days_since_purchase"] / 120).clip(0, 0.99)
    last["risk"] = pd.cut(
        last["churn_probability"],
        bins=[-0.01, 0.33, 0.66, 1.0],
        labels=["Low", "Medium", "High"],
    )
    return last[["customer_id", "days_since_purchase", "churn_probability", "risk"]]


def clv_predictions(data):
    customers = data.get("customers")
    if isinstance(customers, pd.DataFrame) and not customers.empty:
        out = customers.copy()
        if "lifetime_value" in out.columns:
            out["predicted_clv"] = pd.to_numeric(out["lifetime_value"], errors="coerce").fillna(0)
        else:
            out["predicted_clv"] = 0.0
        return out

    tx = _transactions(data)
    if tx.empty or "customer_id" not in tx.columns or "amount" not in tx.columns:
        return pd.DataFrame()

    tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0)
    return tx.groupby("customer_id")["amount"].sum().reset_index(name="predicted_clv")


def model_notes():
    return {
        "Revenue Forecast": "7-day baseline forecast using recent daily revenue and historical volatility.",
        "Churn": "Recency-based MVP probability derived from days since the latest purchase.",
        "CLV": "Uses supplied lifetime_value where available; otherwise aggregates observed transaction value.",
    }
