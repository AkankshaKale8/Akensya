
import streamlit as st
import pandas as pd
import base64
from pathlib import Path

from services.data_service import load_demo_data, process_upload, data_quality, validate_dataset
from services.analytics_service import (
    executive_kpis, channel_performance, journey_funnel,
    campaign_table, customer_segments, sustainability_score
)
from services.ml_service import clv_predictions, churn_predictions, revenue_forecast
from services.recommendation_service import build_recommendations
from services.db_service import save_event, save_dataset, load_user_datasets, delete_dataset, get_profile, supabase_available
from services.auth_service import sign_in, sign_up, sign_out, demo_login, restore_session, supabase_configured
from services.copilot_service import answer_question

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
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "company" not in st.session_state:
    st.session_state.company = "DemoBrand"
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False
if "data" not in st.session_state:
    st.session_state.data = load_demo_data(BASE / "data")


# Load private data for registered accounts; demo mode uses built-in sample data.
if st.session_state.get("demo_mode"):
    data = st.session_state.data
elif st.session_state.get("user_id"):
    private_data = load_user_datasets(st.session_state.user_id)
    data = private_data if private_data else load_demo_data(BASE / "data")
    st.session_state.data = data
else:
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

# ---------------- Authentication ----------------
if not st.session_state.authenticated:
    st.markdown(
        '<div class="hero"><h1>Welcome to Akensya</h1>'
        '<p>AI Decision Intelligence for Smarter Marketing</p>'
        '<span class="pill">Private workspaces</span>'
        '<span class="pill">Marketing intelligence</span></div>',
        unsafe_allow_html=True,
    )

    if not supabase_configured():
        st.warning("Supabase is not configured. Add SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets before using registered accounts.")

    login_tab, signup_tab, demo_tab = st.tabs(["Login", "Create Account", "Demo"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Work email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        if submitted:
            ok, message = sign_in(email, password)
            if ok:
                profile = get_profile(st.session_state.user_id) or {}
                st.session_state.company = profile.get("company") or "DemoBrand"
                st.session_state.user_company = st.session_state.company
                st.session_state.demo_mode = False
                st.session_state.data = load_user_datasets(st.session_state.user_id)
                if not st.session_state.data:
                    st.session_state.data = load_demo_data(BASE / "data")
                save_event("login", "auth", {"email": st.session_state.user_email})
                st.rerun()
            else:
                st.error(message)

    with signup_tab:
        with st.form("signup_form"):
            company = st.text_input("Company name")
            new_email = st.text_input("Work email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            created = st.form_submit_button("Create Account", type="primary", use_container_width=True)
        if created:
            if len(new_password) < 8:
                st.error("Password must be at least 8 characters.")
            elif not company.strip():
                st.error("Company name is required.")
            else:
                ok, message = sign_up(new_email, new_password, company)
                if ok:
                    if st.session_state.get("user_id"):
                        from services.db_service import save_profile
                        save_profile(st.session_state.user_id, new_email.strip().lower(), company.strip())
                    st.success(message)
                else:
                    st.error(message)

    with demo_tab:
        st.caption("Use the demo environment with built-in sample data.")
        with st.form("demo_login"):
            demo_email_input = st.text_input("Demo email", value=st.secrets.get("DEMO_EMAIL", "demo@akensya.ai"))
            demo_password_input = st.text_input("Demo password", type="password")
            demo_submit = st.form_submit_button("Enter Demo", type="primary", use_container_width=True)
        if demo_submit:
            if demo_login(demo_email_input, demo_password_input):
                st.session_state.data = load_demo_data(BASE / "data")
                st.rerun()
            else:
                st.error("Invalid demo credentials.")

    st.stop()

# Restore active Supabase session when possible.
if not st.session_state.get("demo_mode") and not st.session_state.get("user_id"):
    restore_session()

# ---------------- Navigation ----------------
st.sidebar.image(str(ASSET), width=190)
st.sidebar.caption("INSIGHTS. PREDICT. ACT.")
st.sidebar.divider()

nav = {
    "🏠 Executive Dashboard": "Executive Dashboard",
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
st.sidebar.caption(st.session_state.get("user_email", ""))
if st.sidebar.button("Log out", use_container_width=True):
    save_event("logout", "auth", {"email": st.session_state.get("user_email", "")})
    sign_out()
    st.rerun()

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
    topbar("Data Hub", "Upload, validate, replace and manage the data that powers your private Akensya workspace.")

    t1, t2, t3 = st.tabs(["Current Data", "Upload / Replace", "Delete Dataset"])

    with t1:
        for entity in ["customers", "campaigns", "transactions", "interactions", "sustainability"]:
            frame = data.get(entity)
            if isinstance(frame, pd.DataFrame) and not frame.empty:
                q = data_quality(frame)
                st.markdown(f"**{entity.title()}** · {q['records']:,} records · Quality {q['score']}%")
        st.info("Registered-account datasets are stored under the authenticated Supabase user ID. Demo data remains local to the demo environment.")

    with t2:
        entity = st.selectbox("Dataset", ["customers", "campaigns", "transactions", "interactions", "sustainability"])
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded:
            try:
                raw = pd.read_csv(uploaded)
                valid, errors = validate_dataset(entity, raw)
                if not valid:
                    st.error("This file cannot be used as " + entity + ". " + " ".join(errors))
                else:
                    cleaned = process_upload(entity, uploaded)
                    q = data_quality(cleaned)
                    st.success(f"{entity.title()} validated successfully.")
                    st.metric("Quality Score", f"{q['score']}%")
                    st.dataframe(cleaned.head(20), use_container_width=True, hide_index=True)

                    if st.button(f"Save / Replace {entity.title()}", type="primary"):
                        if st.session_state.get("demo_mode"):
                            st.session_state.data[entity] = cleaned
                            st.success(f"{entity.title()} updated in the demo session.")
                        elif st.session_state.get("user_id"):
                            save_dataset(st.session_state.user_id, entity, cleaned)
                            st.session_state.data[entity] = cleaned
                            st.success(f"{entity.title()} saved to your private workspace.")
                        st.rerun()
            except Exception as exc:
                st.error(f"Upload failed: {exc}")

    with t3:
        entity = st.selectbox("Dataset to delete", ["customers", "campaigns", "transactions", "interactions", "sustainability"], key="delete_entity")
        if st.button(f"Delete {entity.title()}", type="secondary"):
            if st.session_state.get("demo_mode"):
                st.session_state.data.pop(entity, None)
            elif st.session_state.get("user_id"):
                delete_dataset(st.session_state.user_id, entity)
                st.session_state.data.pop(entity, None)
            st.success(f"{entity.title()} dataset deleted.")
            st.rerun()

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
    topbar("Ask Akensya", "Ask questions about your active company's marketing data and receive grounded answers.")
    question = st.text_area(
        "Ask Akensya anything...",
        placeholder="Why did our ROI decline? Which customers need retention? What should we do next?"
    )
    if st.button("Ask Akensya", type="primary"):
        answer = answer_question(question, data)
        st.markdown(f'<div class="insight"><b>AKENSYA</b><br>{answer}</div>', unsafe_allow_html=True)
        st.caption("Answers are generated from the active account's analytics context. Optional LLM mode requires OPENAI_API_KEY.")

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
    st.info(f"Authenticated as {st.session_state.get("user_email", "Demo user")}.")
    st.subheader("Database")
    st.info("SQLite is included as a local/demo event store. Production persistence should use PostgreSQL/Supabase or another managed database.")
