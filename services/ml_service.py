
import numpy as np
import pandas as pd

def clv_predictions(data):
    c = data["customers"][["customer_id","name","acquisition_channel","lifetime_value"]].copy()
    tx = data["transactions"].groupby("customer_id").agg(
        orders=("transaction_id","nunique"),
        revenue=("amount","sum"),
        avg_order_value=("amount","mean")
    ).reset_index()
    x = c.merge(tx,on="customer_id",how="left").fillna(0)
    x["predicted_clv"] = x["revenue"]*(1+np.log1p(x["orders"])) + x["avg_order_value"]*2
    return x[["customer_id","name","acquisition_channel","predicted_clv"]]

def churn_predictions(data):
    tx = data["transactions"].copy()
    last = tx.groupby("customer_id")["date"].max().reset_index(name="last_purchase")
    x = data["customers"][["customer_id","name","lifetime_value"]].merge(last,on="customer_id",how="left")
    anchor = tx["date"].max()
    x["days_since_purchase"] = (anchor-x["last_purchase"]).dt.days.fillna(365)
    x["churn_probability"] = (x["days_since_purchase"]/180).clip(0,1)
    x["risk_band"] = pd.cut(x["churn_probability"],[-.01,.33,.66,1.01],labels=["Low","Medium","High"])
    return x

def revenue_forecast(transactions):
    x = transactions.groupby("date")["amount"].sum().sort_index().to_frame("revenue")
    x["forecast"] = x["revenue"].rolling(7,min_periods=1).mean()
    last = float(x["forecast"].iloc[-1])
    future_dates = pd.date_range(x.index.max()+pd.Timedelta(days=1),periods=14)
    future = pd.DataFrame({"forecast":last},index=future_dates)
    hist = x[["forecast"]]
    return pd.concat([hist,future])
