import os, json
import pandas as pd
from .analytics_service import executive_kpis, channel_performance, campaign_table, customer_segments
from .ml_service import churn_predictions, clv_predictions, revenue_forecast
from .recommendation_service import build_recommendations


def evidence_context(data):
    k=executive_kpis(data); ctx={"executive_kpis":k}
    for name,fn,args in [
        ("channels",channel_performance,(data.get("campaigns",pd.DataFrame()),)),
        ("campaigns",campaign_table,(data.get("campaigns",pd.DataFrame()),)),
        ("segments",customer_segments,(data.get("customers",pd.DataFrame()),)),
        ("churn",churn_predictions,(data,)),
        ("clv",clv_predictions,(data,)),
        ("recommendations",build_recommendations,(data,)),
    ]:
        try:
            obj=fn(*args); ctx[name]=obj.head(20).to_dict("records") if isinstance(obj,pd.DataFrame) else obj
        except Exception as e: ctx[name]={"error":str(e)}
    try:
        fc=revenue_forecast(data.get("transactions",pd.DataFrame())); ctx["forecast"]=fc.tail(14).to_dict("records")
    except Exception: pass
    return ctx


def _deterministic(question,data):
    q=question.lower(); k=executive_kpis(data); ctx=evidence_context(data)
    if any(x in q for x in ["revenue forecast","forecast","next month","next 30"]):
        fc=pd.DataFrame(ctx.get("forecast",[]));
        if not fc.empty and "forecast" in fc:
            vals=pd.to_numeric(fc["forecast"],errors="coerce").dropna(); return f"Revenue forecast: the model projects approximately ₹{vals.iloc[-1]:,.0f} for the last forecast point in the current horizon. The forecast is based on the active transaction dataset and should be treated as directional."
    if "churn" in q:
        ch=pd.DataFrame(ctx.get("churn",[]));
        if not ch.empty: return f"The active dataset contains {len(ch):,} customers in the churn-risk model. {int((ch.risk_band.astype(str)=='High').sum()):,} are currently in the High risk band. Prioritize high-risk customers with high CLV for retention actions."
    if "clv" in q or "lifetime value" in q:
        cl=pd.DataFrame(ctx.get("clv",[]));
        if not cl.empty: return f"Average predicted CLV is ₹{pd.to_numeric(cl.predicted_clv,errors='coerce').mean():,.0f}. The highest-value customers can be found in CLV Prediction, where the estimate combines observed transaction value and order frequency."
    if "campaign" in q or "roas" in q or "roi" in q:
        cp=pd.DataFrame(ctx.get("campaigns",[]));
        if not cp.empty and "roas" in cp:
            best=cp.sort_values("roas",ascending=False).iloc[0]; worst=cp.sort_values("roas").iloc[0]
            return f"Current account ROAS is {k['roas']:.2f}x. {best.get('campaign_name','Top campaign')} has the highest observed ROAS at {float(best.roas):.2f}x, while {worst.get('campaign_name','lowest campaign')} is lowest at {float(worst.roas):.2f}x. Review spend reallocation in Prescriptive Analytics."
    if "segment" in q:
        sg=pd.DataFrame(ctx.get("segments",[]));
        if not sg.empty:
            best=sg.sort_values("avg_clv",ascending=False).iloc[0]; return f"The highest-value segment in the active customer dataset is {best['segment']}, with average CLV of ₹{float(best.avg_clv):,.0f}."
    if "recommend" in q or "what should" in q or "next best" in q or "action" in q:
        rec=pd.DataFrame(ctx.get("recommendations",[]));
        if not rec.empty: return "Based on the current data, the highest-priority action is: " + str(rec.iloc[0]["title"]) + ". Evidence: " + str(rec.iloc[0]["reason"]) + "."
    return f"I analysed the active Akensya dataset. Current revenue is ₹{k['revenue']:,.0f}, spend is ₹{k['spend']:,.0f}, and ROAS is {k['roas']:.2f}x. Ask me about revenue, campaigns/ROAS, churn, CLV, segments, forecasts, recommendations, or sustainability and I will ground the answer in the available data."


def answer_question(question,data,company="your company"):
    question=(question or "").strip()
    if not question: return "Please enter a question about your marketing data."
    ctx=evidence_context(data)
    api_key=os.getenv("OPENAI_API_KEY")
    model=os.getenv("OPENAI_MODEL","gpt-4o-mini")
    if api_key:
        try:
            from openai import OpenAI
            client=OpenAI(api_key=api_key)
            system=("You are Akensya, a marketing decision-intelligence analyst. Answer only from the supplied evidence context. "
                    "Do not invent metrics. If the data is insufficient, say what is missing. Explain evidence, uncertainty, and next-best action when useful. "
                    "Never reveal another user's data. Keep answers concise but analytical.")
            response=client.chat.completions.create(model=model,temperature=0.2,messages=[{"role":"system","content":system},{"role":"user","content":f"Company: {company}\nQuestion: {question}\nEvidence JSON:\n{json.dumps(ctx,default=str)[:30000]}"}])
            return response.choices[0].message.content
        except Exception:
            pass
    return _deterministic(question,data)
