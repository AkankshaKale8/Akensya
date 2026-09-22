from __future__ import annotations

import json
import os

from services.analytics_service import executive_kpis, channel_performance, customer_segments, sustainability_score
from services.ml_service import revenue_forecast, churn_predictions, clv_predictions, model_notes
from services.recommendation_service import build_recommendations


def _context(data):
    k = executive_kpis(data)
    recs = build_recommendations(data)
    ctx = {
        "executive_kpis": k,
        "channel_performance": channel_performance(data).head(10).to_dict(orient="records"),
        "recommendations": recs.head(5).to_dict(orient="records"),
        "sustainability_score": sustainability_score(data),
        "forecast": revenue_forecast(data).head(7).to_dict(orient="records"),
        "churn_sample": churn_predictions(data).head(20).to_dict(orient="records"),
        "clv_sample": clv_predictions(data).head(20).to_dict(orient="records"),
        "model_notes": model_notes(),
    }
    return ctx


def _rule_answer(question, data):
    q = (question or "").lower().strip()
    k = executive_kpis(data)

    if not q:
        return "Ask about revenue, ROAS, campaigns, churn, CLV, sustainability, forecasts, or next-best actions."

    if any(x in q for x in ["roi", "roas"]):
        return f"Current blended ROAS is {k['roas']:.2f}x based on the active account's campaign and transaction data."

    if any(x in q for x in ["revenue", "sales"]):
        return f"Recorded revenue in the active dataset is ₹{k['revenue']:,.0f}."

    if any(x in q for x in ["churn", "retention"]):
        return f"The current recency-based churn signal is approximately {k['churn_risk']:.1f}% elevated-risk customers."

    if any(x in q for x in ["clv", "lifetime value", "customer value"]):
        return f"Average supplied customer lifetime value is ₹{k['avg_clv']:,.0f}."

    if any(x in q for x in ["sustain", "green", "carbon", "emission"]):
        return f"The current illustrative sustainability score is {k['green_score']:.1f}/100."

    recs = build_recommendations(data)
    if len(recs):
        return f"Akensya's current next-best action is: {recs.iloc[0]['title']}. {recs.iloc[0]['reason']}"

    return "Akensya could not find a matching metric in the current account dataset."


def answer_question(question, data):
    """Use deterministic analytics by default; optionally add an OpenAI explanation."""
    base = _rule_answer(question, data)
    api_key = os.getenv("OPENAI_API_KEY")

    try:
        import streamlit as st
        api_key = api_key or st.secrets.get("OPENAI_API_KEY")
        model = st.secrets.get("OPENAI_MODEL", "gpt-4o-mini")
    except Exception:
        model = "gpt-4o-mini"

    if not api_key:
        return base

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        context = json.dumps(_context(data), default=str)[:12000]
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are Akensya Copilot. Answer only from the supplied account analytics context. "
                        "Do not invent metrics. Be concise and explain the relevant evidence."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\nAnalytics context:\n{context}",
                },
            ],
        )
        return response.output_text
    except Exception:
        return base
