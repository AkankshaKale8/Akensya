
import pandas as pd

def build_recommendations(data):
    campaigns = data["campaigns"].copy()
    campaigns["roas"] = campaigns["revenue"]/campaigns["spend"].replace(0,pd.NA)
    avg_roas = campaigns["roas"].mean()
    best = campaigns.sort_values("roas",ascending=False).iloc[0]
    worst = campaigns.sort_values("roas",ascending=True).iloc[0]
    high_value = int((data["customers"]["lifetime_value"] >= data["customers"]["lifetime_value"].quantile(.75)).sum())
    return pd.DataFrame([
        {"id":1,"priority":"HIGH","title":f"Increase {best.channel} / {best.campaign_name} budget","reason":f"Observed ROAS is {best.roas:.2f}x versus account average of {avg_roas:.2f}x.","impact":"Potentially higher incremental revenue; validate with an experiment."},
        {"id":2,"priority":"MEDIUM","title":f"Review {worst.channel} spend","reason":f"{worst.campaign_name} has the lowest observed ROAS in the sample.","impact":"Potential efficiency improvement through reallocation."},
        {"id":3,"priority":"HIGH","title":"Launch retention campaign","reason":f"{high_value} customers are in the top value quartile; combine value and churn signals.","impact":"Protect high-value revenue and improve retention."},
        {"id":4,"priority":"MEDIUM","title":"Run sustainability-aware budget scenario","reason":"Compare estimated emissions against reach and ROAS before reallocating media.","impact":"Potentially lower estimated impact with monitored performance."},
    ])
