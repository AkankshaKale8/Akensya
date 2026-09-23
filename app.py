from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from services.auth_service import sign_in, sign_up, sign_out, demo_login, supabase_configured
from services.data_service import (
    normalize_data,
    validate_dataset,
    data_quality,
    load_demo_data,
    DATASET_SPECS,
)
from services.db_service import (
    save_dataset,
    load_dataset,
    load_user_datasets,
    delete_dataset,
)
from services.analytics_service import (
    executive_kpis,
    campaign_table,
    customer_segments,
    journey_funnel,
    sustainability_score,
)
from services.ml_service import (
    revenue_forecast,
    churn_predictions,
    clv_predictions,
    model_notes,
)
from services.recommendation_service import build_recommendations
from services.copilot_service import answer

BASE = Path(__file__).parent
ASSET = BASE / "assets" / "akensya_logo.png"

st.set_page_config(
    page_title="Akensya | Decision Intelligence",
    page_icon=str(ASSET) if ASSET.exists() else "📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Session ----------
if "auth" not in st.session_state:
    st.session_state.auth = None
if "active_data" not in st.session_state:
    st.session_state.active_data = {}
if "navigation" not in st.session_state:
    st.session_state.navigation = "🏠 Executive Dashboard"

# ---------- Styling ----------
st.markdown(
    """
<style>
:root{--navy:#07174A;--blue:#1259D6;--cyan:#16A6E8;--muted:#6F7890;--border:#E6EAF2;}
.stApp{background:#F7F9FC;}
.ak-top{display:flex;align-items:center;gap:18px;padding:22px 26px;border:1px solid var(--border);border-radius:18px;background:#fff;margin-bottom:22px;}
.ak-top img{width:78px;height:78px;object-fit:contain;border-radius:12px;}
.ak-top h1{margin:0;color:var(--navy);font-size:30px;}
.ak-top p{margin:5px 0 0;color:var(--muted);}
.login-shell{max-width:900px;margin:0 auto;padding-top:18px;}
.login-logo{text-align:center;margin-bottom:12px;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#07174A 0%,#1556CF 100%);}
section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] span{color:#fff !important;}
section[data-testid="stSidebar"] button{background:#fff !important;color:#07174A !important;border:1px solid #D7E2F5 !important;border-radius:10px !important;font-weight:700 !important;}
section[data-testid="stSidebar"] button p,section[data-testid="stSidebar"] button span{color:#07174A !important;}
section[data-testid="stSidebar"] button:hover{background:#EAF2FF !important;color:#07174A !important;}
section[data-testid="stSidebar"] button[kind="secondary"]{background:#fff !important;color:#C62828 !important;border:1px solid #F1B8B8 !important;font-weight:700 !important;}
section[data-testid="stSidebar"] button[kind="secondary"] p,section[data-testid="stSidebar"] button[kind="secondary"] span{color:#C62828 !important;}
section[data-testid="stSidebar"] button[kind="secondary"]:hover{background:#FFF1F1 !important;border-color:#D95353 !important;}
div[data-testid="stMarkdownContainer"]:empty{display:none !important;}
footer{visibility:hidden;}
</style>
""",
    unsafe_allow_html=True,
)


def page_header(title: str, subtitle: str = ""):
    if ASSET.exists():
        logo_html = f'<img src="{ASSET.as_posix()}" alt="Akensya">'
    else:
        logo_html = ""
    st.markdown(
        f'<div class="ak-top">{logo_html}<div><h1>{title}</h1><p>{subtitle}</p></div></div>',
        unsafe_allow_html=True,
    )


def demo_data():
    return load_demo_data(BASE / "data")


def refresh_data():
    auth = st.session_state.auth or {}
    if auth.get("demo"):
        st.session_state.active_data = demo_data()
        return
    uid = auth.get("user_id")
    if not uid:
        st.session_state.active_data = {}
        return
    loaded = load_user_datasets(uid)
    st.session_state.active_data = {
        k: v for k, v in loaded.items() if isinstance(v, pd.DataFrame) and not v.empty
    }


def show_login():
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    if ASSET.exists():
        st.markdown('<div class="login-logo">', unsafe_allow_html=True)
        st.image(str(ASSET), width=150)
        st.markdown('</div>', unsafe_allow_html=True)

    st.title("Welcome to Akensya")
    st.caption("AI Decision Intelligence for Smarter Marketing")

    login_tab, signup_tab, demo_tab = st.tabs(["Login", "Create Account", "Demo"])

    with login_tab:
        with st.form("akensya_login"):
            email = st.text_input("Work email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        if submitted:
            ok, message = sign_in(email, password)
            if ok:
                st.session_state.auth = {
                    "user_id": st.session_state.get("user_id"),
                    "email": st.session_state.get("user_email", email.strip().lower()),
                    "company_name": st.session_state.get("company", "My Brand"),
                    "demo": False,
                }
                st.session_state.active_data = {}
                refresh_data()
                st.rerun()
            st.error(message)

    with signup_tab:
        with st.form("akensya_signup"):
            company = st.text_input("Company / Brand name")
            email = st.text_input("Work email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
        if submitted:
            if not company.strip():
                st.error("Enter your company or brand name.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 8:
                st.error("Use at least 8 characters.")
            else:
                ok, message = sign_up(email, password, company)
                if ok:
                    st.success(message)
                else:
                    st.error(message)

    with demo_tab:
        st.info("Demo Mode uses Akensya's built-in sample data and does not modify a registered brand workspace.")
        if st.button("Continue with Demo Account", type="primary", use_container_width=True):
            if demo_login("demo@akensya.ai", "Akensya@123"):
                st.session_state.auth = {
                    "user_id": "demo",
                    "email": "demo@akensya.ai",
                    "company_name": "DemoBrand",
                    "demo": True,
                }
                st.session_state.active_data = demo_data()
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


if not st.session_state.auth:
    show_login()

# ---------- Active account ----------
auth = st.session_state.auth
if not st.session_state.active_data:
    refresh_data()
data = st.session_state.active_data

# ---------- Navigation: unchanged page set/order ----------
pages = [
    "🏠 Executive Dashboard",
    "📊 Data Hub",
    "📈 Descriptive Analytics",
    "🔮 Predictive Analytics",
    "🎯 Prescriptive Analytics",
    "👥 Customer Intelligence",
    "↳ Customer Journey",
    "↳ Customer Segmentation",
    "↳ CLV Prediction",
    "📢 Campaign Intelligence",
    "🌱 Sustainability",
    "🤖 Ask Akensya",
    "⚙ Settings",
]

with st.sidebar:
    if ASSET.exists():
        st.image(str(ASSET), width=170)
    st.caption("INSIGHTS. PREDICT. ACT.")
    st.divider()
    choice = st.radio(
        "Go to",
        pages,
        index=pages.index(st.session_state.navigation) if st.session_state.navigation in pages else 0,
        label_visibility="collapsed",
    )
    st.session_state.navigation = choice
    st.divider()
    st.write(f"**Company:** {auth.get('company_name', 'My Brand')}")
    st.caption(auth.get("email", ""))
    if auth.get("demo"):
        st.caption("Demo Mode")
    if st.button("Logout", key="logout_button", use_container_width=True, type="secondary"):
        try:
            sign_out()
        except Exception:
            pass
        st.session_state.clear()
        st.rerun()


# ---------- Pages ----------
if choice == "🏠 Executive Dashboard":
    page_header("Executive Dashboard", "A single view of performance, risk and decisions.")
    k = executive_kpis(data)
    cols = st.columns(4)
    cols[0].metric("Revenue", f"{k['revenue']:,.0f}")
    cols[1].metric("Campaign ROAS", f"{k['roas']:.2f}x")
    cols[2].metric("Average CLV", f"{k['avg_clv']:,.0f}")
    cols[3].metric("Churn Risk", f"{k['churn_risk']:.1f}%")
    st.subheader("Decision signals")
    recs = build_recommendations(data)
    if isinstance(recs, pd.DataFrame) and not recs.empty:
        st.dataframe(recs, use_container_width=True, hide_index=True)
    else:
        st.info("No decision signals are available yet.")

elif choice == "📊 Data Hub":
    page_header("Data Hub", "Upload, replace and delete the datasets powering Akensya.")
    if auth.get("demo"):
        st.info("Demo Mode is read-only. Create a brand account to upload and manage private datasets.")

    t1, t2 = st.tabs(["My Datasets", "Upload / Replace"])
    with t1:
        if not data:
            st.info("No datasets are currently available.")
        for name, df in data.items():
            c1, c2 = st.columns([5, 1])
            c1.write(f"**{name.title()}** · {len(df):,} rows · {len(df.columns)} columns")
            if c2.button("Delete", key=f"delete_{name}") and not auth.get("demo"):
                if delete_dataset(auth["user_id"], name):
                    refresh_data()
                    st.rerun()
    with t2:
        uploaded = st.file_uploader("Upload CSV", type=["csv"], key="dataset_upload")
        if uploaded:
            dtype = st.selectbox("Dataset type", list(DATASET_SPECS.keys()), key="dataset_type")
            raw = pd.read_csv(uploaded)
            clean = normalize_data(dtype, raw)
            valid, errors = validate_dataset(dtype, clean)
            quality = data_quality(clean)
            st.write(f"**Detected/selected type:** {dtype}")
            st.metric("Data Quality", f"{quality['score']:.0f}%")
            st.dataframe(clean.head(20), use_container_width=True)
            if not valid:
                st.error("; ".join(errors))
            elif auth.get("demo"):
                st.warning("Demo Mode cannot persist uploaded datasets. Create a brand account first.")
            elif st.button("Save / Replace Dataset", type="primary"):
                result = save_dataset(auth["user_id"], dtype, clean)
                if result:
                    refresh_data()
                    st.success(f"{dtype.title()} dataset saved/replaced successfully.")
                    st.rerun()
                st.error("The dataset could not be saved. Check Supabase configuration and RLS policies.")

elif choice == "📈 Descriptive Analytics":
    page_header("Descriptive Analytics", "Understand what happened.")
    k = executive_kpis(data)
    st.dataframe(pd.DataFrame([k]), use_container_width=True, hide_index=True)
    camp = campaign_table(data)
    if not camp.empty:
        st.subheader("Campaign performance")
        st.dataframe(camp, use_container_width=True, hide_index=True)

elif choice == "🔮 Predictive Analytics":
    page_header("Predictive Analytics", "Estimate what is likely to happen next.")
    t1, t2, t3 = st.tabs(["Revenue Forecast", "Churn Prediction", "Model Notes"])
    with t1:
        fc = revenue_forecast(data)
        if fc.empty:
            st.warning("Upload dated transaction/revenue data to generate a forecast.")
        else:
            chart_col = "date" if "date" in fc.columns else fc.columns[0]
            st.line_chart(fc.set_index(chart_col)["forecast"])
            st.dataframe(fc, use_container_width=True, hide_index=True)
    with t2:
        risk = churn_predictions(data)
        if risk.empty:
            st.warning("Upload transactions containing customer_id and date to generate churn risk.")
        else:
            high = int((risk["risk"].astype(str) == "High").sum())
            st.metric("High Risk Customers", high)
            st.dataframe(risk, use_container_width=True, hide_index=True)
    with t3:
        for title, note in model_notes().items():
            st.markdown(f"**{title}**")
            st.write(note)

elif choice == "🎯 Prescriptive Analytics":
    page_header("Prescriptive Analytics", "Move from prediction to the next-best action.")
    recs = build_recommendations(data)
    if isinstance(recs, pd.DataFrame) and not recs.empty:
        st.dataframe(recs, use_container_width=True, hide_index=True)
    else:
        st.info("No recommendations available yet.")

elif choice == "👥 Customer Intelligence":
    page_header("Customer Intelligence", "Understand who your customers are and where value is created.")
    c = data.get("customers", pd.DataFrame())
    if c.empty:
        st.warning("Upload a customers dataset.")
    else:
        st.dataframe(customer_segments(data), use_container_width=True, hide_index=True)

elif choice == "↳ Customer Journey":
    page_header("Customer Journey", "See interaction stages and customer movement.")
    j = journey_funnel(data)
    if j.empty:
        st.warning("Upload interactions data containing a stage column.")
    else:
        st.dataframe(j, use_container_width=True, hide_index=True)

elif choice == "↳ Customer Segmentation":
    page_header("Customer Segmentation", "Group customers by observable value characteristics.")
    c = data.get("customers", pd.DataFrame())
    if c.empty:
        st.warning("Upload customers data.")
    else:
        st.dataframe(customer_segments(data), use_container_width=True, hide_index=True)

elif choice == "↳ CLV Prediction":
    page_header("CLV Prediction", "Estimate customer value to prioritize retention and growth.")
    clv = clv_predictions(data)
    if clv.empty:
        st.warning("Upload customers or transactions data to estimate CLV.")
    else:
        st.metric("Average predicted CLV", f"{pd.to_numeric(clv['predicted_clv'], errors='coerce').mean():,.0f}")
        st.dataframe(clv, use_container_width=True, hide_index=True)

elif choice == "📢 Campaign Intelligence":
    page_header("Campaign Intelligence", "Compare campaigns and identify efficiency signals.")
    camp = campaign_table(data)
    if camp.empty:
        st.warning("Upload campaign data.")
    else:
        st.dataframe(camp, use_container_width=True, hide_index=True)

elif choice == "🌱 Sustainability":
    page_header("Sustainability", "Estimate marketing sustainability indicators.")
    st.metric("Sustainability Score", f"{sustainability_score(data):.0f}/100")
    st.caption("Prototype estimate. Environmental calculations should be replaced with verified measurement data for production use.")

elif choice == "🤖 Ask Akensya":
    page_header("Ask Akensya", "Ask questions about your active marketing data, insights, predictions and decisions.")
    q = st.text_area("Ask Akensya anything", placeholder="Why is ROI changing? Which campaigns need attention? What is my churn risk?")
    if st.button("Ask Akensya", type="primary") and q.strip():
        st.info(answer(q, data))

elif choice == "⚙ Settings":
    page_header("Settings", "Account and application settings.")
    st.write(f"**Email:** {auth.get('email', '')}")
    st.write(f"**Account:** {'Demo' if auth.get('demo') else 'Registered brand account'}")
    st.write(f"**Supabase configured:** {'Yes' if supabase_configured() else 'No'}")
    st.caption("Registered account datasets are isolated by user_id and protected by Supabase Row Level Security.")
