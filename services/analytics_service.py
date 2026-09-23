import numpy as np
import pandas as pd


def _df(data, key):
    return data.get(key, pd.DataFrame()).copy()


def executive_kpis(data):
    c, camp, tx, sus = _df(data,"customers"), _df(data,"campaigns"), _df(data,"transactions"), _df(data,"sustainability")
    revenue = float(tx["amount"].sum()) if "amount" in tx else float(camp["revenue"].sum()) if "revenue" in camp else 0.0
    spend = float(camp["spend"].sum()) if "spend" in camp else 0.0
    roas = revenue / spend if spend else 0.0
    avg_clv = float(c["lifetime_value"].mean()) if "lifetime_value" in c and len(c) else 0.0
    conversions = int(camp["conversions"].sum()) if "conversions" in camp else 0
    green_score = 0
    if not sus.empty and "estimated_emissions" in sus:
        emissions = float(sus["estimated_emissions"].sum())
        green_score = int(max(0,min(100,92-emissions/120)))
    return {"revenue": revenue, "spend": spend, "roas": roas, "avg_clv": avg_clv, "conversions": conversions, "churn_risk": 0.0, "green_score": green_score}


def channel_performance(campaigns):
    if campaigns.empty or "channel" not in campaigns: return pd.DataFrame(columns=["channel","spend","revenue","conversions","impressions","clicks","roas","ctr"])
    x = campaigns.groupby("channel").agg(spend=("spend","sum"), revenue=("revenue","sum"), conversions=("conversions","sum"), impressions=("impressions","sum"), clicks=("clicks","sum")).reset_index()
    x["roas"] = x["revenue"] / x["spend"].replace(0,np.nan)
    x["ctr"] = x["clicks"] / x["impressions"].replace(0,np.nan)
    return x


def journey_funnel(interactions):
    if interactions.empty or "stage" not in interactions: return pd.DataFrame(columns=["stage","customers","interactions","conversions","conversion_rate"])
    x = interactions.groupby("stage").agg(customers=("customer_id","nunique"), interactions=("customer_id","size"), conversions=("converted","sum") if "converted" in interactions else ("customer_id","size")).reset_index()
    x["conversion_rate"] = x["conversions"] / x["interactions"].replace(0,np.nan)
    return x


def campaign_table(campaigns):
    if campaigns.empty: return pd.DataFrame(columns=["campaign_id","campaign_name","channel","spend","revenue","roas","conversion_rate"])
    x = campaigns.copy()
    x["roas"] = x["revenue"] / x["spend"].replace(0,np.nan) if {"revenue","spend"}.issubset(x.columns) else np.nan
    x["conversion_rate"] = x["conversions"] / x["clicks"].replace(0,np.nan) if {"conversions","clicks"}.issubset(x.columns) else np.nan
    cols=[c for c in ["campaign_id","campaign_name","channel","spend","revenue","roas","conversion_rate"] if c in x.columns]
    return x[cols].sort_values("roas",ascending=False) if "roas" in x else x[cols]


def customer_segments(customers):
    if customers.empty or "customer_id" not in customers or "lifetime_value" not in customers:
        return pd.DataFrame(columns=["segment","customers","avg_clv"])
    x=customers.copy(); q1,q2=x["lifetime_value"].quantile([.33,.66])
    x["segment"]=np.select([x["lifetime_value"]<=q1,x["lifetime_value"]<=q2],["Value Builder","Growth Customer"],default="High Value")
    return x.groupby("segment").agg(customers=("customer_id","nunique"),avg_clv=("lifetime_value","mean")).reset_index()


def sustainability_score(data):
    s=_df(data,"sustainability"); camp=_df(data,"campaigns")
    emissions=float(s["estimated_emissions"].sum()) if "estimated_emissions" in s else 0.0
    reach=int(camp["impressions"].sum()) if "impressions" in camp else 0
    score=int(max(0,min(100,92-emissions/120))) if not s.empty else 0
    return {"score":score,"emissions":emissions,"reach":reach,"recommendation":"Shift a portion of spend from the highest-emission channel toward channels with lower estimated impact while monitoring projected reach and efficiency."}
