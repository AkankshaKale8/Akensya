import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def clv_predictions(data):
    c=data.get("customers",pd.DataFrame()).copy(); tx=data.get("transactions",pd.DataFrame()).copy()
    if c.empty or "customer_id" not in c: return pd.DataFrame(columns=["customer_id","name","acquisition_channel","predicted_clv"])
    cols=[x for x in ["customer_id","name","acquisition_channel","lifetime_value"] if x in c.columns]
    base=c[cols].copy()
    if tx.empty or "customer_id" not in tx or "amount" not in tx: base["predicted_clv"]=base.get("lifetime_value",0).fillna(0); return base[[x for x in ["customer_id","name","acquisition_channel","predicted_clv"] if x in base.columns]]
    txg=tx.groupby("customer_id").agg(orders=("transaction_id","nunique") if "transaction_id" in tx else ("customer_id","size"),revenue=("amount","sum"),avg_order_value=("amount","mean")).reset_index()
    x=base.merge(txg,on="customer_id",how="left").fillna(0)
    historical=x.get("lifetime_value",pd.Series(0,index=x.index)).astype(float)
    x["predicted_clv"]=np.maximum(x["revenue"]*(1+np.log1p(x["orders"])) + x["avg_order_value"]*2, historical)
    return x[[x for x in ["customer_id","name","acquisition_channel","predicted_clv"] if x in x.columns]]


def churn_predictions(data):
    tx=data.get("transactions",pd.DataFrame()).copy(); c=data.get("customers",pd.DataFrame()).copy()
    if c.empty or "customer_id" not in c: return pd.DataFrame(columns=["customer_id","name","churn_probability","risk_band"])
    if tx.empty or "customer_id" not in tx or "date" not in tx:
        x=c[[x for x in ["customer_id","name","lifetime_value"] if x in c.columns]].copy(); x["days_since_purchase"]=365; x["churn_probability"]=1.0; x["risk_band"]="High"; return x
    last=tx.groupby("customer_id")["date"].max().reset_index(name="last_purchase"); x=c[[x for x in ["customer_id","name","lifetime_value"] if x in c.columns]].merge(last,on="customer_id",how="left")
    anchor=tx["date"].max(); x["days_since_purchase"]=(anchor-x["last_purchase"]).dt.days.fillna(365)
    x["churn_probability"]=(x["days_since_purchase"]/180).clip(0,1)
    x["risk_band"]=pd.cut(x["churn_probability"],[-.01,.33,.66,1.01],labels=["Low","Medium","High"])
    return x


def revenue_forecast(transactions, periods=14):
    if transactions.empty or "date" not in transactions or "amount" not in transactions: return pd.DataFrame(columns=["date","actual","forecast"])
    tx=transactions.copy(); tx["date"]=pd.to_datetime(tx["date"],errors="coerce"); tx=tx.dropna(subset=["date"])
    hist=tx.groupby("date")["amount"].sum().sort_index().to_frame("actual")
    if len(hist)>=5:
        y=hist["actual"].values; X=np.arange(len(y)).reshape(-1,1); model=LinearRegression().fit(X,y); future_X=np.arange(len(y),len(y)+periods).reshape(-1,1); pred=np.maximum(model.predict(future_X),0)
        hist["forecast"]=np.nan; future_dates=pd.date_range(hist.index.max()+pd.Timedelta(days=1),periods=periods); future=pd.DataFrame({"date":future_dates,"actual":np.nan,"forecast":pred}).set_index("date")
    else:
        rolling=hist["actual"].rolling(7,min_periods=1).mean(); hist["forecast"]=rolling; future_dates=pd.date_range(hist.index.max()+pd.Timedelta(days=1),periods=periods); future=pd.DataFrame({"actual":np.nan,"forecast":float(rolling.iloc[-1])},index=future_dates)
    out=pd.concat([hist,future]).reset_index().rename(columns={"index":"date"}); return out
