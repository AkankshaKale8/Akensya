
import numpy as np
import pandas as pd

def executive_kpis(data):
    c = data["customers"]
    camp = data["campaigns"]
    tx = data["transactions"]
    sus = data["sustainability"]
    revenue = float(tx["amount"].sum())
    spend = float(camp["spend"].sum())
    roas = revenue / spend if spend else 0
    return {
        "revenue": revenue,
        "spend": spend,
        "roas": roas,
        "avg_clv": float(c["lifetime_value"].mean()),
        "conversions": int(camp["conversions"].sum()),
        "churn_risk": 14.2,
        "green_score": int(max(0,min(100,100-sus["estimated_emissions"].mean()/2))),
    }

def channel_performance(campaigns):
    x = campaigns.groupby("channel").agg(
        spend=("spend","sum"), revenue=("revenue","sum"), conversions=("conversions","sum"),
        impressions=("impressions","sum"), clicks=("clicks","sum")
    ).reset_index()
    x["roas"] = x["revenue"] / x["spend"].replace(0,np.nan)
    x["ctr"] = x["clicks"] / x["impressions"].replace(0,np.nan)
    return x

def journey_funnel(interactions):
    x = interactions.groupby("stage").agg(
        customers=("customer_id","nunique"),
        interactions=("customer_id","size"),
        conversions=("converted","sum")
    ).reset_index()
    x["conversion_rate"] = x["conversions"] / x["interactions"].replace(0,np.nan)
    return x

def campaign_table(campaigns):
    x = campaigns.copy()
    x["roas"] = x["revenue"] / x["spend"].replace(0,np.nan)
    x["conversion_rate"] = x["conversions"] / x["clicks"].replace(0,np.nan)
    return x[["campaign_id","campaign_name","channel","spend","revenue","roas","conversion_rate"]].sort_values("roas",ascending=False)

def customer_segments(customers):
    x = customers.copy()
    q1,q2 = x["lifetime_value"].quantile([.33,.66])
    x["segment"] = np.select(
        [x["lifetime_value"]<=q1, x["lifetime_value"]<=q2],
        ["Value Builder","Growth Customer"], default="High Value"
    )
    return x.groupby("segment").agg(customers=("customer_id","nunique"),avg_clv=("lifetime_value","mean")).reset_index()

def sustainability_score(data):
    s = data["sustainability"]
    emissions = float(s["estimated_emissions"].sum())
    reach = int(data["campaigns"]["impressions"].sum())
    score = int(max(0,min(100,92-emissions/120)))
    return {
        "score":score,
        "emissions":emissions,
        "reach":reach,
        "recommendation":"Shift a portion of spend from the highest-emission channel toward channels with lower estimated impact while monitoring projected reach and efficiency."
    }
