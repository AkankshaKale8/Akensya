from __future__ import annotations
import base64
from pathlib import Path
import pandas as pd
import streamlit as st

from services.auth_service import sign_in, sign_up, sign_out
from services.data_service import prepare, validate, quality_score, dataset_type_from_name
from services.db_service import save_dataset, load_dataset, delete_dataset, list_datasets
from services.analytics_service import executive_kpis, campaign_performance, customer_segments, journey, sustainability_score
from services.ml_service import revenue_forecast, churn_prediction, clv_prediction, model_notes
from services.recommendation_service import build_recommendations
from services.copilot_service import answer

BASE = Path(__file__).parent
ASSET = BASE / "assets" / "akensya_logo.png"

st.set_page_config(page_title="Akensya | Decision Intelligence", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

if "auth" not in st.session_state:
    st.session_state.auth = None
if "active_data" not in st.session_state:
    st.session_state.active_data = {}
if "datasets_local" not in st.session_state:
    st.session_state.datasets_local = {}

def logo_b64():
    try:
        return base64.b64encode(ASSET.read_bytes()).decode()
    except Exception:
        return ""

def topbar(title, subtitle=""):
    logo = logo_b64()
    img = f'<img src="data:image/png;base64,{logo}" alt="Akensya" />' if logo else ""
    st.markdown(f"""
    <div class="ak-top">
      {img}
      <div><h1>{title}</h1><p>{subtitle}</p></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
:root{--navy:#07174a;--blue:#1259d6;--cyan:#16a6e8;--purple:#6335d9;}
.stApp{background:#f7f9fc;}
.ak-top{display:flex;align-items:center;gap:18px;padding:22px 26px;border:1px solid #e6eaf2;border-radius:18px;background:white;margin-bottom:22px;}
.ak-top img{width:78px;height:78px;object-fit:contain;border-radius:12px;}
.ak-top h1{margin:0;color:#07174a;font-size:30px;}
.ak-top p{margin:5px 0 0;color:#6f7890;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#07174a 0%,#1556cf 100%);}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span{color:#FFFFFF !important;}
section[data-testid="stSidebar"] button{
    background:#FFFFFF !important;
    color:#07174A !important;
    border:1px solid #D7E2F5 !important;
    border-radius:10px !important;
    font-weight:700 !important;
}
section[data-testid="stSidebar"] button p,
section[data-testid="stSidebar"] button span{color:#07174A !important;}
section[data-testid="stSidebar"] button:hover{background:#EAF2FF !important;color:#07174A !important;}
section[data-testid="stSidebar"] button[kind="secondary"]{
    background:#FFFFFF !important;
    color:#C62828 !important;
    border:1px solid #F1B8B8 !important;
    font-weight:700 !important;
}
section[data-testid="stSidebar"] button[kind="secondary"] p,
section[data-testid="stSidebar"] button[kind="secondary"] span{color:#C62828 !important;}
section[data-testid="stSidebar"] button[kind="secondary"]:hover{background:#FFF1F1 !important;border-color:#D95353 !important;}
.metric-card{background:white;border:1px solid #e6eaf2;border-radius:16px;padding:18px;}
/* Prevent blank Streamlit containers from appearing as a white pill above the logo. */
div[data-testid="stMarkdownContainer"]:empty{display:none !important;}
div[data-testid="stAlert"]:empty{display:none !important;}
</style>
""", unsafe_allow_html=True)

def demo_csv(name):
    path = BASE / "data" / name
    if path.exists():
        try: return prepare(pd.read_csv(path))
        except Exception: pass
    return pd.DataFrame()

def demo_data():
    return {
        "customers": demo_csv("customers.csv"),
        "campaigns": demo_csv("campaigns.csv"),
        "interactions": demo_csv("interactions.csv"),
        "transactions": demo_csv("transactions.csv"),
        "sustainability": demo_csv("sustainability.csv"),
    }

def show_login():
    # Keep the login header clean: no empty placeholder/white pill above the logo.
    st.markdown("<div style='height:3vh;'></div>", unsafe_allow_html=True)
    if ASSET.exists():
        st.image(str(ASSET), width=150)
    st.title("Welcome to Akensya")
    st.caption("AI Decision Intelligence for Smarter Marketing")
    tab1,tab2=st.tabs(["Login","Create Account"])
    with tab1:
        with st.form("login"):
            email=st.text_input("Email")
            password=st.text_input("Password",type="password")
            if st.form_submit_button("Login",type="primary"):
                result=sign_in(email,password)
                if result.get("ok"):
                    st.session_state.auth=result
                    st.rerun()
                st.error(result.get("error","Login failed."))
        st.info("Demo account: demo@akensya.ai / Akensya@123")
    with tab2:
        with st.form("signup"):
            company=st.text_input("Company / Brand name")
            email=st.text_input("Work email")
            password=st.text_input("Password",type="password")
            confirm=st.text_input("Confirm password",type="password")
            if st.form_submit_button("Create Account",type="primary"):
                if password != confirm:
                    st.error("Passwords do not match.")
                elif len(password)<8:
                    st.error("Use at least 8 characters.")
                else:
                    result=sign_up(email,password,company)
                    if result.get("ok"):
                        st.success("Account created. Check your email if confirmation is enabled, then log in.")
                    else: st.error(result.get("error","Could not create account."))
    st.stop()

if not st.session_state.auth:
    show_login()

auth=st.session_state.auth
user_id=auth.get("user_id","demo")
is_demo=auth.get("demo",False)

def load_active_data():
    if is_demo:
        return demo_data()
    data={}
    for row in list_datasets(user_id):
        name=row.get("dataset_name","")
        df=load_dataset(user_id,name)
        if df is not None:
            data[dataset_type_from_name(name)] = prepare(df)
    return data

if not st.session_state.active_data:
    st.session_state.active_data=load_active_data()

data=st.session_state.active_data

with st.sidebar:
    if ASSET.exists(): st.image(ASSET,width=170)
    st.caption("INSIGHTS. PREDICT. ACT.")
    st.divider()
    st.write("Navigation")
    pages=[
        "🏠 Executive Dashboard","📊 Data Hub","📈 Descriptive Analytics","🔮 Predictive Analytics",
        "🎯 Prescriptive Analytics","👥 Customer Intelligence","↳ Customer Journey","↳ Customer Segmentation",
        "↳ CLV Prediction","📢 Campaign Intelligence","🌱 Sustainability","🤖 Ask Akensya","⚙ Settings"
    ]
    choice=st.radio("Go to",pages,label_visibility="collapsed")
    st.divider()
    st.write(f"**Company:** {'DemoBrand' if is_demo else auth.get('company_name','My Company')}")
    st.caption(auth.get("email",""))
    if st.button(
        "Logout",
        key="logout_button",
        use_container_width=True,
        type="secondary"
    ):
        try:
            sign_out()
        except Exception:
            pass

        # Clear the current workspace and authentication state.
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.session_state.auth = None
        st.session_state.active_data = {}
        st.session_state.datasets_local = {}
        st.rerun()

def page_header(title,subtitle):
    topbar(title,subtitle)

if choice=="🏠 Executive Dashboard":
    page_header("Executive Dashboard","A single view of performance, risk and decisions.")
    k=executive_kpis(data)
    cols=st.columns(4)
    cols[0].metric("Revenue",f"{k['revenue']:,.0f}")
    cols[1].metric("Campaign ROI",f"{k['roi']:.2f}x")
    cols[2].metric("Average CLV",f"{k['avg_clv']:,.0f}")
    cols[3].metric("Conversions",f"{k['conversions']:,.0f}")
    st.subheader("Decision signals")
    recs=build_recommendations(data)
    if recs:
        for r in recs[:3]:
            st.info(f"**{r['title']}** — {r['reason']}")
    else: st.success("No immediate decision signals were generated from the active data.")

elif choice=="📊 Data Hub":
    page_header("Data Hub","Upload, validate, replace and delete the datasets powering Akensya.")
    if is_demo: st.info("You are using Demo Mode. Built-in sample data is protected; create an account to manage private datasets.")
    tabs=st.tabs(["My Datasets","Upload / Replace"])
    with tabs[0]:
        if is_demo:
            for key,df in data.items():
                st.write(f"**{key.title()}** — {len(df):,} records")
        else:
            rows=list_datasets(user_id)
            if not rows: st.info("No datasets uploaded yet.")
            for row in rows:
                name=row["dataset_name"]
                c1,c2=st.columns([5,1])
                c1.write(f"**{name}** · {row.get('row_count',0):,} rows")
                if c2.button("Delete",key="del_"+name):
                    res=delete_dataset(user_id,name)
                    if res.get("ok"):
                        st.session_state.active_data=load_active_data()
                        st.rerun()
                    else: st.error(res.get("error","Delete failed."))
    with tabs[1]:
        file=st.file_uploader("Upload CSV",type=["csv"])
        if file:
            raw=pd.read_csv(file)
            name=st.text_input("Dataset name",value=file.name)
            dtype=dataset_type_from_name(name)
            ok,missing,clean=validate(raw,dtype)
            q=quality_score(clean)
            st.write(f"**Detected type:** {dtype}")
            st.metric("Data Quality",f"{q['score']:.0f}%")
            st.dataframe(clean.head(20),use_container_width=True)
            if not ok:
                st.error("This dataset cannot be used for the selected dataset type. Missing: "+", ".join(missing))
            else:
                if st.button("Save / Replace Dataset",type="primary"):
                    if is_demo:
                        st.error("Create an account to persist your own datasets.")
                    else:
                        res=save_dataset(user_id,name,clean)
                        if res.get("ok"):
                            st.session_state.active_data=load_active_data()
                            st.success("Dataset saved. Existing dataset with the same name was replaced.")
                        else: st.error(res.get("error","Save failed."))

elif choice=="📈 Descriptive Analytics":
    page_header("Descriptive Analytics","Understand what happened.")
    k=executive_kpis(data)
    st.write(pd.DataFrame([k]))
    camp=campaign_performance(data.get("campaigns"))
    if not camp.empty:
        st.subheader("Campaign performance")
        st.dataframe(camp,use_container_width=True)
        if "roas" in camp: st.bar_chart(camp.set_index(camp.columns[0])["roas"])

elif choice=="🔮 Predictive Analytics":
    page_header("Predictive Analytics","Estimate what is likely to happen next.")
    t1,t2,t3=st.tabs(["Revenue Forecast","Churn Prediction","Model Notes"])
    with t1:
        fc=revenue_forecast(data.get("campaigns"),data.get("transactions"))
        if fc.empty: st.warning("Upload dated revenue data to generate a forecast.")
        else:
            st.line_chart(fc.set_index("period")["forecast"])
            st.dataframe(fc,use_container_width=True)
    with t2:
        c=data.get("customers",pd.DataFrame())
        if c.empty: st.warning("Upload a customers dataset.")
        else:
            risk=churn_prediction(c)
            st.metric("High Risk Customers",int((risk["risk"]=="High").sum()))
            st.dataframe(risk,use_container_width=True)
    with t3:
        for k,v in model_notes().items():
            st.markdown(f"**{k}**")
            st.write(v)

elif choice=="🎯 Prescriptive Analytics":
    page_header("Prescriptive Analytics","Move from prediction to the next-best action.")
    recs=build_recommendations(data)
    if not recs: st.success("No recommendations available yet.")
    for r in recs:
        with st.container(border=True):
            st.subheader(r["title"]); st.write(r["reason"]); st.caption(r["impact"])

elif choice=="👥 Customer Intelligence":
    page_header("Customer Intelligence","Understand who your customers are and where value is created.")
    c=data.get("customers",pd.DataFrame())
    if c.empty: st.warning("Upload a customers dataset.")
    else:
        st.dataframe(customer_segments(c).head(100),use_container_width=True)

elif choice=="↳ Customer Journey":
    page_header("Customer Journey","See interaction stages and customer movement.")
    j=journey(data.get("interactions"))
    st.dataframe(j,use_container_width=True) if not j.empty else st.warning("Upload interactions data with customer_id and interaction_type.")

elif choice=="↳ Customer Segmentation":
    page_header("Customer Segmentation","Group customers by observable value characteristics.")
    c=data.get("customers",pd.DataFrame())
    st.dataframe(customer_segments(c),use_container_width=True) if not c.empty else st.warning("Upload customers data.")

elif choice=="↳ CLV Prediction":
    page_header("CLV Prediction","Estimate customer value to prioritize retention and growth.")
    c=data.get("customers",pd.DataFrame())
    if c.empty: st.warning("Upload customers data.")
    else:
        clv=clv_prediction(c,data.get("transactions"))
        st.metric("Average predicted CLV",f"{clv['predicted_clv'].mean():,.0f}")
        st.dataframe(clv,use_container_width=True)

elif choice=="📢 Campaign Intelligence":
    page_header("Campaign Intelligence","Compare campaigns and identify efficiency signals.")
    camp=campaign_performance(data.get("campaigns"))
    st.dataframe(camp,use_container_width=True) if not camp.empty else st.warning("Upload campaign data.")

elif choice=="🌱 Sustainability":
    page_header("Sustainability","Estimate marketing sustainability indicators.")
    st.metric("Sustainability Score",f"{sustainability_score(data.get('sustainability')):.0f}/100")
    st.caption("Prototype estimate. Environmental calculations should be replaced with verified measurement data for production use.")

elif choice=="🤖 Ask Akensya":
    page_header("Ask Akensya","Ask questions about your active marketing data, insights, predictions and decisions.")
    q=st.text_area("Ask Akensya anything",placeholder="Why is ROI changing? Which campaigns need attention? What is my churn risk?")
    if st.button("Ask Akensya",type="primary") and q.strip():
        st.info(answer(q,data))

elif choice=="⚙ Settings":
    page_header("Settings","Account and application settings.")
    st.write(f"**Email:** {auth.get('email','')}")
    st.write(f"**Account:** {'Demo' if is_demo else 'Registered brand account'}")
    st.caption("Registered account datasets are isolated by user_id and protected by Supabase Row Level Security.")
