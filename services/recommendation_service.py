from __future__ import annotations

import pandas as pd

from services.analytics_service import executive_kpis, channel_performance


def build_recommendations(data):
    k = executive_kpis(data)
    rows = []

    if k["roas"] and k["roas"] < 2:
        rows.append({
            "title": "Review low-efficiency media",
            "reason": f"Current blended ROAS is {k['roas']:.2f}x.",
            "impact": "Improve spend efficiency by reallocating budget toward stronger channels.",
        })

    if k["churn_risk"] > 25:
        rows.append({
            "title": "Prioritize retention",
            "reason": f"Approximately {k['churn_risk']:.1f}% of customers show elevated recency risk.",
            "impact": "Use targeted retention journeys for high-risk customers.",
        })

    channels = channel_performance(data)
    if not channels.empty and "roas" in channels.columns:
        best = channels.sort_values("roas", ascending=False).iloc[0]
        rows.append({
            "title": f"Scale {best['channel']}",
            "reason": f"It currently has the strongest observed ROAS at {best['roas']:.2f}x.",
            "impact": "Test incremental budget while monitoring marginal returns.",
        })

    if not rows:
        rows.append({
            "title": "Connect more live data",
            "reason": "The current demo dataset is limited.",
            "impact": "Additional first-party campaign and customer data will improve recommendations.",
        })

    return pd.DataFrame(rows)
