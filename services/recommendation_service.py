import pandas as pd

def build_recommendations(data):
    campaigns=data.get("campaigns",pd.DataFrame()).copy(); customers=data.get("customers",pd.DataFrame()).copy()
    rows=[]
    if not campaigns.empty and {"revenue","spend"}.issubset(campaigns.columns):
        campaigns["roas"]=campaigns["revenue"]/campaigns["spend"].replace(0,pd.NA); avg=float(campaigns["roas"].mean()) if len(campaigns) else 0
        if len(campaigns):
            best=campaigns.sort_values("roas",ascending=False).iloc[0]; worst=campaigns.sort_values("roas",ascending=True).iloc[0]
            rows.append({"id":1,"priority":"HIGH","title":f"Increase {best.get('channel','channel')} / {best.get('campaign_name','top campaign')} budget","reason":f"Observed ROAS is {float(best.roas):.2f}x versus account average of {avg:.2f}x.","impact":"Potentially higher incremental revenue; validate with an experiment."})
            rows.append({"id":2,"priority":"MEDIUM","title":f"Review {worst.get('channel','channel')} spend","reason":f"{worst.get('campaign_name','The lowest-performing campaign')} has the lowest observed ROAS in the active dataset.","impact":"Potential efficiency improvement through reallocation."})
    if not customers.empty and "lifetime_value" in customers:
        high=int((customers["lifetime_value"]>=customers["lifetime_value"].quantile(.75)).sum())
        rows.append({"id":3,"priority":"HIGH","title":"Launch retention campaign","reason":f"{high} customers are in the top value quartile; combine value and churn signals.","impact":"Protect high-value revenue and improve retention."})
    rows.append({"id":4,"priority":"MEDIUM","title":"Run sustainability-aware budget scenario","reason":"Compare estimated emissions against reach and ROAS before reallocating media.","impact":"Potentially lower estimated impact with monitored performance."})
    return pd.DataFrame(rows)
