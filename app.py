
import streamlit as st
import pandas as pd
import base64
from pathlib import Path

from services.data_service import load_demo_data, process_upload, data_quality
from services.analytics_service import (
    executive_kpis, channel_performance, journey_funnel,
    campaign_table, customer_segments, sustainability_score
)
from services.ml_service import clv_predictions, churn_predictions, revenue_forecast
from services.recommendation_service import build_recommendations
from services.db_service import save_event

BASE = Path(__file__).parent
ASSET = BASE / "assets" / "akensya_logo.png"
LOGO_DATA = base64.b64encode(ASSET.read_bytes()).decode("utf-8")

st.set_page_config(
    page_title="Akensya | Decision Intelligence",
    page_icon=str(ASSET),
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- Brand system ----------------
st.markdown("""
<style>
:root{
  --ak-navy:#07164A;
  --ak-blue:#1267D6;
  --ak-cyan:#12A9E8;
  --ak-purple:#6225D9;
  --ak-violet:#8B36E8;
  --ak-ink:#101828;
  --ak-muted:#667085;
  --ak-bg:#F6F8FC;
  --ak-border:#E4E7EC;
  --ak-green:#12B76A;
}
.block-container{max-width:1500px;padding:1.1rem 2rem 3rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#07164A 0%,#101B5B 60%,#201064 100%);}
[data-testid="stSidebar"] *{color:#fff !important;}
[data-testid="stSidebar"] .stRadio label{padding:5px 0;}
.ak-top{display:flex;align-items:center;gap:18px;padding:14px 18px;background:#fff;border:1px solid var(--ak-border);border-radius:18px;margin-bottom:18px;}
.ak-top img{width:76px;height:76px;object-fit:contain;}
.ak-top h1{margin:0;color:var(--ak-navy);font-size:1.65rem;letter-spacing:.2px;}
.ak-top p{margin:.2rem 0 0;color:var(--ak-muted);}
.hero{padding:28px;border-radius:22px;background:linear-gradient(135deg,#07164A 0%,#17236B 52%,#1267D6 100%);color:white;margin-bottom:20px;}
.hero h1{font-size:2.2rem;margin:0 0 7px;}
.hero p{margin:0;color:#DDE8FF;font-size:1.02rem;}
.pill{display:inline-block;padding:6px 10px;border-radius:99px;background:#FFFFFF18;border:1px solid #FFFFFF30;font-size:.78rem;margin-right:6px;margin-top:12px;}
.kpi{background:#fff;border:1px solid var(--ak-border);border-radius:16px;padding:17px;min-height:108px;box-shadow:0 3px 14px #1018280a;}
.kpi-label{font-size:.78rem;color:var(--ak-muted);}
.kpi-value{font-size:1.55rem;font-weight:750;color:var(--ak-navy);margin-top:5px;}
.kpi-delta{font-size:.78rem;color:var(--ak-green);margin-top:3px;}
.section{font-size:1.15rem;font-weight:750;color:var(--ak-navy);margin:1.25rem 0 .7rem;}
.insight{padding:16px;border-radius:14px;background:#F2F7FF;border-left:4px solid var(--ak-blue);color:var(--ak-ink);}
.action{padding:17px;border:1px solid #D9E2F5;border-radius:15px;background:#fff;}
.action strong{color:var(--ak-navy);}
.status{padding:10px 12px;border-radius:10px;background:#F2F4F7;color:#475467;font-size:.82rem;}
footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------- Session ----------------
if "data" not in st.session_state:
    st.session_state.data = load_demo_data(BASE/"data")
if "company" not in st.session_state:
    st.session_state.company = "DemoBrand"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = True
if "events" not in st.session_state:
    st.session_state.events = []

data = st.session_state.data

def money(v):
    return f"₹{v/1_000_000:.1f}M" if abs(v) >= 1_000_000 else f"₹{v/100_000:.1f}L"

def topbar(title, subtitle):
    st.markdown(
        f"""<div class="ak-top">
        <img src="data:image/png;base64,{LOGO_DATA}" alt="Akensya logo"/>
        <div><h1>{title}</h1><p>{subtitle}</p></div>
        </div>""",
        unsafe_allow_html=True,
    )

def kpi(label, value, delta=""):
    st.markdown(
        f"""<div class="kpi"><div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div><div class="kpi-delta">{delta}</div></div>""",
        unsafe_allow_html=True
    )

# ---------------- Login ----------------
if not st.session_state.authenticated:
    st.image(str(ASSET), width=210)
    st.title("Welcome to Akensya")
    st.caption("AI Decision Intelligence for Smarter Marketing")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login", use_container_width=True):
            st.session_state.authenticated = True
            st.rerun()
    if st.button("Create Account", use_container_width=True):
        st.session_state.authenticated = True
        st.rerun()
    st.stop()

# ---------------- Navigation ----------------
st.sidebar.image(str(ASSET), width=190)
st.sidebar.caption("INSIGHTS. PREDICT. ACT.")
st.sidebar.divider()

nav = {
    "🏠 Executive Dashboard": "Executive Dashboard",
    "🚀 Onboarding": "Onboarding",
    "🗄️ Data Hub": "Data Hub",
    "📈 Descriptive Analytics": "Descriptive Analytics",
    "🔮 Predictive Analytics": "Predictive Analytics",
    "🎯 Prescriptive Analytics": "Prescriptive Analytics",
    "👥 Customer Intelligence": "Customer Intelligence",
    "   ↳ Customer Journey": "Customer Journey",
    "   ↳ Customer Segmentation": "Customer Segmentation",
    "   ↳ CLV Prediction": "CLV Prediction",
    "📢 Campaign Intelligence": "Campaign Intelligence",
    "🌱 Sustainability": "Sustainability",
    "🤖 Ask Akensya": "Ask Akensya",
    "⚙️ Settings": "Settings",
}
selected = st.sidebar.radio("Navigation", list(nav.keys()))
page = nav[selected]
st.sidebar.divider()
st.sidebar.markdown(f"**Company:** {st.session_state.company}")
st.sidebar.markdown('<div class="status">Demo data active · API-ready architecture</div>', unsafe_allow_html=True)

# ---------------- Pages ----------------
if page == "Executive Dashboard":
    topbar("Executive Intelligence", "One decision view for revenue, marketing, customers and sustainable growth.")
    k = executive_kpis(data)
    cols = st.columns(5)
    for col, (lab,val,delta) in zip(cols, [
        ("Revenue", money(k["revenue"]), "↑ 12.4%"),
        ("Campaign ROI", f'{k["roas"]:.1f}x', "↑ 8.2%"),
        ("Customer CLV", money(k["avg_clv"]), "↑ 6.7%"),
        ("Churn Risk", f'{k["churn_risk"]:.1f}%', "↓ 3.1%"),
        ("Green Score", f'{k["green_score"]}/100', "↑ 4 pts"),
    ]):
        with col: kpi(lab,val,delta)
    st.markdown('<div class="section">Revenue trend</div>', unsafe_allow_html=True)
    st.line_chart(data["transactions"].groupby("date")["amount"].sum())
    st.markdown('<div class="section">Top AI recommendations</div>', unsafe_allow_html=True)
    recs = build_recommendations(data)
    for _, r in recs.head(3).iterrows():
        st.markdown(f"""<div class="action"><strong>{r['title']}</strong><br>
        {r['reason']}<br><b>Expected impact:</b> {r['impact']}</div><br>""", unsafe_allow_html=True)

elif page == "Data Hub":
    topbar("Data Hub", "Upload, validate and prepare the data layer that powers every Akensya module.")
    st.markdown('<div class="section">Data sources</div>', unsafe_allow_html=True)
    t1,t2,t3 = st.tabs(["Sample Data","Upload CSV","API Connectors"])
    with t1:
        st.success("Akensya is running with built-in sample data.")
        st.dataframe(data["customers"].head(12), use_container_width=True, hide_index=True)
    with t2:
        entity = st.selectbox("Dataset", ["customers","campaigns","interactions","sustainability"])
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded:
            new_df = process_upload(entity, uploaded)
            score = data_quality(new_df)["score"]
            st.session_state.data[entity] = new_df
            save_event("upload", entity, {"rows": len(new_df), "quality_score": score})
            st.success(f"{entity} loaded successfully.")
            q = data_quality(new_df)
            a,b,c,d = st.columns(4)
            with a: kpi("Quality Score", f"{q['score']}%")
            with b: kpi("Records", f"{q['records']:,}")
            with c: kpi("Missing", f"{q['missing_pct']:.1f}%")
            with d: kpi("Duplicates", f"{q['duplicate_pct']:.1f}%")
            st.dataframe(new_df.head(20), use_container_width=True, hide_index=True)
    with t3:
        st.info("API connectors are scaffolded for the next phase.")
        st.write("Planned: Google Analytics 4 · Google Ads · Meta Ads · Salesforce · HubSpot · Shopify")
        st.code("API → connector → normalize_data() → database → analytics → Akensya UI")

elif page == "Descriptive Analytics":
    topbar("Descriptive Analytics", "Understand what happened across campaigns, channels and customers.")
    k = executive_kpis(data)
    cols = st.columns(4)
    for col, pair in zip(cols,[("Revenue",money(k["revenue"])),("Spend",money(k["spend"])),("ROAS",f'{k["roas"]:.2f}x'),("Conversions",f'{k["conversions"]:,}')]):
        with col: kpi(*pair)
    st.markdown('<div class="section">Channel performance</div>', unsafe_allow_html=True)
    ch = channel_performance(data["campaigns"])
    st.dataframe(ch, use_container_width=True, hide_index=True)
    st.bar_chart(ch.set_index("channel")["revenue"])
    st.markdown('<div class="insight"><b>AI Insight</b><br>Compare conversion contribution with spend share to identify channels where efficiency and scale differ.</div>', unsafe_allow_html=True)

elif page == "Predictive Analytics":
    topbar("Predictive Analytics", "Estimate what is likely to happen next.")
    t1,t2,t3 = st.tabs(["Revenue Forecast","Churn Prediction","Model Notes"])
    with t1:
        fc = revenue_forecast(data["transactions"])
        st.line_chart(fc.set_index("date"))
        st.success("Forecast is generated from historical sample data. Replace with a trained forecasting model from Colab for production.")
    with t2:
        churn = churn_predictions(data)
        a,b,c = st.columns(3)
        with a: kpi("High Risk", f"{(churn.risk_band=='High').sum():,}")
        with b: kpi("Medium Risk", f"{(churn.risk_band=='Medium').sum():,}")
        with c: kpi("Low Risk", f"{(churn.risk_band=='Low').sum():,}")
        st.dataframe(churn.sort_values("churn_probability",ascending=False), use_container_width=True, hide_index=True)
    with t3:
        st.write("Colab workflow: data cleaning → feature engineering → model training → evaluation → export → GitHub → Streamlit inference.")

elif page == "Prescriptive Analytics":
    topbar("Prescriptive Analytics", "Move from prediction to the next-best action.")
    recs = build_recommendations(data)
    for _, r in recs.iterrows():
        st.markdown(f"""<div class="action"><strong>{r['priority']} · {r['title']}</strong>
        <br>{r['reason']}<br><b>Expected impact:</b> {r['impact']}</div><br>""", unsafe_allow_html=True)
        c1,c2 = st.columns([1,5])
        with c1:
            if st.button("Review", key="review_"+str(r["id"])):
                save_event("recommendation_review", str(r["id"]), {"title":r["title"]})
                st.success("Recommendation marked for review.")

elif page == "Customer Intelligence":
    st.session_state._customer_page = "Customer Intelligence"
    topbar("Customer Intelligence", "Understand who your customers are and where value is created.")
    st.write("Use the submenu in the sidebar for Journey, Segmentation and CLV Prediction.")
    seg = customer_segments(data["customers"])
    st.dataframe(seg, use_container_width=True, hide_index=True)

elif page == "Customer Journey":
    topbar("Customer Journey", "Identify the largest drop-offs from awareness to loyalty.")
    f = journey_funnel(data["interactions"])
    st.bar_chart(f.set_index("stage")["customers"])
    st.dataframe(f, use_container_width=True, hide_index=True)
    if len(f):
        biggest = f.sort_values("conversion_rate").iloc[0]
        st.markdown(f'<div class="insight"><b>Journey signal</b><br>{biggest["stage"]} currently has the lowest stage conversion rate in the sample.</div>', unsafe_allow_html=True)

elif page == "Customer Segmentation":
    topbar("Customer Segmentation", "Group customers by observable value and engagement characteristics.")
    seg = customer_segments(data["customers"])
    st.dataframe(seg, use_container_width=True, hide_index=True)
    st.bar_chart(seg.set_index("segment")["customers"])

elif page == "CLV Prediction":
    topbar("CLV Prediction", "Estimate customer value to prioritize retention and growth.")
    clv = clv_predictions(data)
    a,b,c = st.columns(3)
    with a: kpi("Average CLV", money(clv.predicted_clv.mean()))
    with b: kpi("High Value", money(clv.predicted_clv.quantile(.9)))
    with c: kpi("Customers", f"{len(clv):,}")
    st.dataframe(clv.sort_values("predicted_clv",ascending=False), use_container_width=True, hide_index=True)
    st.bar_chart(clv.head(20).set_index("customer_id")["predicted_clv"])

elif page == "Campaign Intelligence":
    topbar("Campaign Intelligence", "Compare campaign economics and identify optimization opportunities.")
    ct = campaign_table(data["campaigns"])
    st.dataframe(ct, use_container_width=True, hide_index=True)
    campaign = st.selectbox("Select campaign", ct["campaign_name"].tolist())
    row = ct[ct.campaign_name==campaign].iloc[0]
    a,b,c,d = st.columns(4)
    with a: kpi("Spend",money(row.spend))
    with b: kpi("Revenue",money(row.revenue))
    with c: kpi("ROAS",f"{row.roas:.2f}x")
    with d: kpi("Conversion",f"{row.conversion_rate:.1%}")
    st.markdown(f'<div class="insight"><b>Campaign explanation</b><br>{campaign} generated {row.conversion_rate:.1%} conversion rate with {row.roas:.2f}x ROAS in the sample.</div>', unsafe_allow_html=True)

elif page == "Sustainability":
    topbar("Green Intelligence™", "Track estimated marketing impact alongside commercial performance.")
    s = sustainability_score(data)
    a,b,c = st.columns(3)
    with a: kpi("Green Score",f'{s["score"]}/100',"Illustrative estimate")
    with b: kpi("Estimated emissions",f'{s["emissions"]:.0f} kg',"Sample assumption")
    with c: kpi("Estimated reach",f'{s["reach"]:,}')
    st.bar_chart(data["sustainability"].groupby("channel")["estimated_emissions"].mean())
    st.warning("Sustainability metrics in this academic prototype are illustrative estimates, not verified environmental measurements.")
    st.markdown(f'<div class="insight"><b>Green Recommendation</b><br>{s["recommendation"]}</div>', unsafe_allow_html=True)

elif page == "Ask Akensya":
    topbar("Ask Akensya", "Ask questions about your marketing data and receive evidence-backed prototype insights.")
    question = st.text_area("Ask Akensya anything...", placeholder="Why did our ROI decline this month?")
    if st.button("Ask Akensya", type="primary"):
        k = executive_kpis(data)
        q = question.lower()
        if "roi" in q or "roas" in q:
            answer = f"Based on the sample data, account ROAS is {k['roas']:.2f}x. Review channel-level spend versus revenue and investigate channels with below-average ROAS."
        elif "churn" in q:
            answer = "The churn model identifies customers using recency-based risk in the MVP. Prioritize high-risk customers with high predicted CLV for retention."
        elif "sustain" in q or "green" in q or "carbon" in q:
            answer = "The Green Intelligence module estimates channel-level emissions and creates a relative score. These are illustrative assumptions until verified environmental data is connected."
        else:
            answer = "Akensya found the strongest next step by combining descriptive performance, predictive signals and recommendation rules. Open Prescriptive Analytics to review the current recommendations."
        st.markdown(f'<div class="insight"><b>AKENSYA</b><br>{answer}</div>', unsafe_allow_html=True)
        st.caption("Prototype response generated from current application data. Production version can connect an LLM to governed data retrieval and evidence.")

elif page == "Onboarding":
    topbar("Company Onboarding", "Configure Akensya around your company's decision priorities.")
    with st.form("onboard"):
        company = st.text_input("Company Name", st.session_state.company)
        industry = st.selectbox("Industry",["D2C","E-commerce","Retail","SaaS","Healthcare","Other"])
        size = st.selectbox("Company Size",["1–50","51–250","251–1000","1000+"])
        goals = st.multiselect("Marketing Objectives",["Increase Revenue","Improve Retention","Improve Campaign ROI","Increase Conversion","Reduce Churn","Improve Sustainability"],["Increase Revenue","Improve Campaign ROI"])
        stack = st.multiselect("Marketing Stack",["Salesforce","HubSpot","Google Analytics","Google Ads","Meta Ads","Shopify"])
        if st.form_submit_button("Save & Continue", type="primary"):
            st.session_state.company = company or "DemoBrand"
            save_event("onboarding", st.session_state.company, {"industry":industry,"size":size,"goals":goals,"stack":stack})
            st.success("Onboarding saved. Continue to Data Hub.")

elif page == "Settings":
    topbar("Settings", "Application configuration and deployment information.")
    st.subheader("Architecture")
    st.code("""Google Colab → model experimentation
GitHub → source + sample data + model artifacts
Database/API → persistent application data
Streamlit Cloud → always-on application
Mobile/Desktop browser → end user""")
    st.subheader("Authentication")
    st.info("Prototype authentication uses Streamlit session state. Production should use an identity provider and tenant-aware authorization.")
    st.subheader("Database")
    st.info("SQLite is included as a local/demo event store. Production persistence should use PostgreSQL/Supabase or another managed database.")
    if st.button("Log out"):
        st.session_state.authenticated = False
        st.rerun()
