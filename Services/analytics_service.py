from __future__ import annotations

import numpy as np
import pandas as pd


def _df(data, name):
    value = data.get(name)
    return value.copy() if isinstance(value, pd.DataFrame) else pd.DataFrame()


def _safe_numeric(df, column, default=0.0):
    if column not in df.columns:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce").fillna(default)


def executive_kpis(data):
    transactions = _df(data, "transactions")
    campaigns = _df(data, "campaigns")
    customers = _df(data, "customers")
    sustainability = _df(data, "sustainability")

    revenue = float(_safe_numeric(transactions, "amount").sum())
    if revenue == 0 and "revenue" in campaigns.columns:
        revenue = float(_safe_numeric(campaigns, "revenue").sum())

    spend = float(_safe_numeric(campaigns, "spend").sum())
    roas = revenue / spend if spend > 0 else 0.0

    if "lifetime_value" in customers.columns:
        avg_clv = float(_safe_numeric(customers, "lifetime_value").mean())
    else:
        avg_clv = 0.0

    churn_risk = 0.0
    if not transactions.empty and "customer_id" in transactions.columns and "date" in transactions.columns:
        dates = pd.to_datetime(transactions["date"], errors="coerce").dropna()
        if not dates.empty:
            latest = dates.max()
            last_purchase = transactions.assign(_date=pd.to_datetime(transactions["date"], errors="coerce")).groupby("customer_id")["_date"].max()
            churn_risk = float((latest - last_purchase).dt.days.gt(60).mean() * 100)

    green_score = sustainability_score(data)
    return {
        "revenue": revenue,
        "roas": roas,
        "avg_clv": avg_clv,
        "churn_risk": churn_risk,
        "green_score": green_score,
    }


def channel_performance(data):
    campaigns = _df(data, "campaigns")
    if campaigns.empty:
        return pd.DataFrame(columns=["channel", "spend", "revenue", "roas"])

    channel_col = "channel" if "channel" in campaigns.columns else None
    if not channel_col:
        return pd.DataFrame()

    out = campaigns.copy()
    out["spend"] = _safe_numeric(out, "spend")
    out["revenue"] = _safe_numeric(out, "revenue")
    result = out.groupby(channel_col, dropna=False)[["spend", "revenue"]].sum().reset_index()
    result["roas"] = np.where(result["spend"] > 0, result["revenue"] / result["spend"], 0)
    return result


def journey_funnel(data):
    interactions = _df(data, "interactions")
    if interactions.empty:
        return pd.DataFrame()
    stage = "stage" if "stage" in interactions.columns else None
    if not stage:
        return pd.DataFrame()
    return interactions.groupby(stage).size().reset_index(name="users")


def campaign_table(data):
    campaigns = _df(data, "campaigns")
    if campaigns.empty:
        return campaigns
    out = campaigns.copy()
    out["spend"] = _safe_numeric(out, "spend")
    out["revenue"] = _safe_numeric(out, "revenue")
    out["roas"] = np.where(out["spend"] > 0, out["revenue"] / out["spend"], 0)
    return out


def customer_segments(data):
    customers = _df(data, "customers")
    if customers.empty:
        return pd.DataFrame()

    out = customers.copy()
    if "lifetime_value" not in out.columns:
        out["lifetime_value"] = 0.0
    out["lifetime_value"] = _safe_numeric(out, "lifetime_value")
    q1, q2 = out["lifetime_value"].quantile([0.33, 0.66]).tolist()
    out["segment"] = np.select(
        [
            out["lifetime_value"] <= q1,
            out["lifetime_value"] <= q2,
        ],
        ["Value Developing", "Growth"],
        default="High Value",
    )
    return out


def sustainability_score(data):
    sustainability = _df(data, "sustainability")
    if sustainability.empty:
        return 0.0

    emissions_col = next(
        (c for c in ["estimated_emissions", "emissions", "carbon_kg"] if c in sustainability.columns),
        None,
    )
    if not emissions_col:
        return 0.0

    emissions = _safe_numeric(sustainability, emissions_col)
    total = float(emissions.sum())
    if total <= 0:
        return 100.0

    # Relative illustrative score for the MVP.
    return float(max(0, min(100, round(100 / (1 + total / max(len(sustainability), 1)), 1))))
