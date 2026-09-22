import os
import base64
from pathlib import Path
import pandas as pd
import streamlit as st

from services.data_service import load_demo_data, process_upload, data_quality, schema_report, empty_data, data_status
from services.analytics_service import executive_kpis, channel_performance, journey_funnel, campaign_table, customer_segments, sustainability_score
from services.ml_service import clv_predictions, churn_predictions, revenue_forecast
from services.recommendation_service import build_recommendations
from services.copilot_service import answer_question
from services.db_service import make_store

BASE = Path(__file__).parent
ASSET = BASE / "assets" / "akensya_logo.png"
LOGO_DATA = base64.b64encode(ASSET.read_bytes()).decode("utf-8") if ASSET.exists() else ""

st.set_page_config(page_title="Akensya | Decision Intelligence", page_icon=str(ASSET) if ASSET.exists() else "📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root{--ak-navy:#07164A;--ak-blue:#1267D6;--ak-cyan:#12A9E8;--ak-purple:#6225D9;--ak-violet:#8B36E8;--ak-ink:#101828;--ak-muted:#667085;--ak-bg:#F6F8FC;--ak-border:#E4E7EC;--ak-green:#12B76A;--ak-red:#D92D20}
.block-container{max-width:1500px;padding:1.1rem 2rem 3rem}.stApp{background:var(--ak-bg)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#07164A 0%,#101B5B 60%,#201064 100%)}[data-testid="stSidebar"] *{color:#fff !important}[data-testid="stSidebar"] .stRadio label{padding:5px 0}
.ak-top{display:flex;align-items:center;gap:18px;padding:14px 18px;background:#fff;border:1px solid var(--ak-border);border-radius:18px;margin-bottom:18px}.ak-top img{width:76px;height:76px;object-fit:contain}.ak-top h1{margin:0;color:var(--ak-navy);font-size:1.65rem}.ak-top p{margin:.2rem 0 0;color:var(--ak-muted)}
.hero{padding:28px;border-radius:22px;background:linear-gradient(135deg,#07164A 0%,#17236B 52%,#1267D6 100%);color:white;margin-bottom:20px}.hero h1{font-size:2.2rem;margin:0 0 7px}.hero p{margin:0;color:#DDE8FF;font-size:1.02rem}.pill{display:inline-block;padding:6px 10px;border-radius:99px;background:#FFFFFF18;border:1px solid #FFFFFF30;font-size:.78rem;margin-right:6px;margin-top:12px}
.kpi{background:#fff;border:1px solid var(--ak-border);border-radius:16px;padding:17px;min-height:108px;box-shadow:0 3px 14px #1018280a}.kpi-label{font-size:.78rem;color:var(--ak-muted)}.kpi-value{font-size:1.55rem;font-weight:750;color:var(--ak-navy);margin-top:5px}.kpi-delta{font-size:.78rem;color:var(--ak-green);margin-top:3px}.section{font-size:1.15rem;font-weight:750;color:var(--ak-navy);margin:1.25rem 0 .7rem}.insight{padding:16px;border-radius:14px;background:#F2F7FF;border-left:4px solid var(--ak-blue);color:var(--ak-ink)}.action{padding:17px;border:1px solid #D9E2F5;border-radius:15px;background:#fff}.action strong{color:var(--ak-navy)}.status{padding:10px 12px;border-radius:10px;background:#F2F4F7;color:#475467;font-size:.82rem}.danger{padding:12px;border-radius:10px;background:#FEF3F2;border-left:4px solid var(--ak-red)}.auth-card{max-width:520px;margin:4rem auto;padding:2rem;background:#fff;border:1px solid var(--ak-border);border-radius:22px;box-shadow:0 10px 35px #10182812}
@media(max-width:700px){.block-container{padding:.7rem .7rem 2rem}.ak-top{gap:10px}.ak-top img{width:56px;height:56px}.ak-top h1{font-size:1.25rem}.hero{padding:20px}.hero h1{font-size:1.6rem}}
</style>
""", unsafe_allow_html=True)

# ---------- helpers ----------
def money(v):
    v=float(v or 0)
    if abs(v)>=1_000_000:return f"₹{v/1_000_000:.1f}M"
    if abs(v)>=100_000:return f"₹{v/100_000:.1f}L"
    return f"₹{v:,.0f}"

def topbar(title,subtitle):
    st.markdown(f'<div class="ak-top"><img src="data:image/png;base64,{LOGO_DATA}" alt="Akensya logo"/><div><h1>{title}</h1><p>{subtitle}</p></div></div>',unsafe_allow_html=True)

def kpi(label,value,delta=""):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-delta">{delta}</div></div>',unsafe_allow_html=True)

def configured_store():
    return make_store(st)

def reset_runtime():
    for key in list(st.session_state.keys()):
        if key not in {"supabase_store"}: del st.session_state[key]
    st.rerun()

def current_data():
    if st.session_state.get("mode") == "demo": return st.session_state.demo_data
    store=st.session_state.get("store"); uid=st.session_state.get("user_id")
    if store and uid:
        loaded=store.get_datasets(uid); base=empty_data(); base.update(loaded); return base
    return empty_data()

def auth_screen(store):
    st.markdown('<div class="auth-card">',unsafe_allow_html=True)
    if LOGO_DATA: st.markdown(f'<img src="data:image/png;base64,{LOGO_DATA}" style="width:190px;display:block;margin:0 auto 12px"/>',unsafe_allow_html=True)
    st.title("Welcome to Akensya")
    st.caption("AI Decision Intelligence for Smarter Marketing")
    login_tab, signup_tab, demo_tab = st.tabs(["Login","Create Account","Demo"])
    with login_tab:
        if not store:
            st.warning("Production authentication is not configured yet. Add SUPABASE_URL and SUPABASE_ANON_KEY in Streamlit Secrets to enable secure brand accounts.")
        with st.form("login_form"):
            email=st.text_input("Work email")
            password=st.text_input("Password",type="password")
            submitted=st.form_submit_button("Login",type="primary",use_container_width=True)
        if submitted and store:
            try:
                res=store.sign_in(email.strip(),password)
                session=res.session
                if session:
                    st.session_state.mode="user"; st.session_state.user_id=session.user.id; st.session_state.email=email.strip(); st.session_state.authenticated=True; st.session_state.access_token=session.access_token; st.session_state.refresh_token=session.refresh_token
                    prof=store.profile(session.user.id); st.session_state.company=prof.get("company_name") or "My Brand"
                    st.rerun()
            except Exception as e: st.error(f"Login failed: {e}")
    with signup_tab:
        if not store: st.warning("Secure account creation requires Supabase configuration in Streamlit Secrets.")
        with st.form("signup_form"):
            company=st.text_input("Brand / Company name")
            email=st.text_input("Work email",key="signup_email")
            password=st.text_input("Password",type="password",key="signup_password",help="Use at least 8 characters.")
            password2=st.text_input("Confirm password",type="password")
            submitted=st.form_submit_button("Create Account",type="primary",use_container_width=True)
        if submitted and store:
            if len(password)<8: st.error("Password must be at least 8 characters.")
            elif password!=password2: st.error("Passwords do not match.")
            elif not company.strip(): st.error("Please enter your brand/company name.")
            else:
                try:
                    res=store.sign_up(email.strip(),password,company.strip())
                    if res.session:
                        st.session_state.mode="user"; st.session_state.user_id=res.session.user.id; st.session_state.email=email.strip(); st.session_state.authenticated=True; st.session_state.access_token=res.session.access_token; st.session_state.refresh_token=res.session.refresh_token; st.session_state.company=company.strip(); st.rerun()
                    else: st.success("Account created. Check your email to confirm the account, then return to Login.")
                except Exception as e: st.error(f"Could not create account: {e}")
    with demo_tab:
        st.write("Explore the full product with isolated sample data. Demo data is separate from registered brand accounts.")
        if st.button("Continue as Demo",type="primary",use_container_width=True):
            st.session_state.mode="demo"; st.session_state.user_id="demo"; st.session_state.company="DemoBrand"; st.session_state.authenticated=True; st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)
    st.stop()

# ---------- session/auth ----------
if "store" not in st.session_state: st.session_state.store=configured_store()
if "authenticated" not in st.session_state: st.session_state.authenticated=False
if not st.session_state.authenticated:
    auth_screen(st.session_state.store)

if st.session_state.get("mode")=="demo":
    if "demo_data" not in st.session_state: st.session_state.demo_data=load_demo_data(BASE/"data")
else:
    # Restore Supabase session after Streamlit reruns.
    if st.session_state.get("store") and st.session_state.get("access_token"):
        try: st.session_state.store.set_session(st.session_state.access_token,st.session_state.refresh_token)
        except Exception: pass

data=current_data()

# ---------- sidebar/navigation (preserved) ----------
st.sidebar.image(str(ASSET),width=190)
st.sidebar.caption("INSIGHTS. PREDICT. ACT.")
st.sidebar.divider()
nav={"🏠 Executive Dashboard":"Executive Dashboard","🗄️ Data Hub":"Data Hub","📈 Descriptive Analytics":"Descriptive Analytics","🔮 Predictive Analytics":"Predictive Analytics","🎯 Prescriptive Analytics":"Prescriptive Analytics","👥 Customer Intelligence":"Customer Intelligence","   ↳ Customer Journey":"Customer Journey","   ↳ Customer Segmentation":"Customer Segmentation","   ↳ CLV Prediction":"CLV Prediction","📢 Campaign Intelligence":"Campaign Intelligence","🌱 Sustainability":"Sustainability","🤖 Ask Akensya":"Ask Akensya","⚙️ Settings":"Settings"}
selected=st.sidebar.radio("Navigation",list(nav.keys())); page=nav[selected]
st.sidebar.divider()
mode_label="DEMO" if st.session_state.get("mode")=="demo" else "LIVE ACCOUNT"
st.sidebar.markdown(f"**{st.session_state.get('company','My Brand')}**")
st.sidebar.markdown(f'<div class="status">{mode_label} · {st.session_state.get("email", "Sample workspace")}</div>',unsafe_allow_html=True)
if st.sidebar.button("Log out",use_container_width=True):
    if st.session_state.get("store") and st.session_state.get("mode")=="user": st.session_state.store.sign_out()
    reset_runtime()

# ---------- pages ----------
if page=="Executive Dashboard":
    topbar("Executive Intelligence","One decision view for revenue, marketing, customers and sustainable growth.")
    k=executive_kpis(data); cols=st.columns(5)
    items=[("Revenue",money(k["revenue"]),"From active dataset"),("Campaign ROI",f'{k["roas"]:.1f}x',"Calculated from revenue/spend"),("Customer CLV",money(k["avg_clv"]),"Active customer data"),("Churn Risk",f'{(churn_predictions(data).churn_probability.mean()*100 if not churn_predictions(data).empty else 0):.1f}%',"Behavioral proxy"),("Green Score",f'{k["green_score"]}/100',"Illustrative estimate")]
    for col,(a,b,c) in zip(cols,items):
        with col:kpi(a,b,c)
    st.markdown('<div class="section">Revenue trend</div>',unsafe_allow_html=True)
    tx=data.get("transactions",pd.DataFrame())
    if not tx.empty and {"date","amount"}.issubset(tx.columns): st.line_chart(tx.groupby("date")["amount"].sum())
    else: st.info("Upload a transactions dataset to populate the executive revenue trend.")
    st.markdown('<div class="section">Top AI recommendations</div>',unsafe_allow_html=True)
    recs=build_recommendations(data)
    for _,r in recs.head(3).iterrows(): st.markdown(f'<div class="action"><strong>{r["title"]}</strong><br>{r["reason"]}<br><b>Expected impact:</b> {r["impact"]}</div><br>',unsafe_allow_html=True)

elif page=="Data Hub":
    topbar("Data Hub","Upload, validate, update and delete the data layer that powers every Akensya module.")
    if st.session_state.get("mode")=="demo":
        st.info("Demo workspace: built-in sample datasets are isolated from registered brand data. Uploading in Demo mode changes only this temporary browser session.")
    t1,t2,t3=st.tabs(["My Datasets","Upload / Update","API Connectors"])
    with t1:
        if st.session_state.get("mode")=="user" and st.session_state.get("store"):
            rows=st.session_state.store.list_datasets(st.session_state.user_id)
            if rows:
                st.dataframe(pd.DataFrame([{k:r.get(k) for k in ["dataset_type","file_name","row_count","updated_at"]} for r in rows]),use_container_width=True,hide_index=True)
                entity=st.selectbox("Select dataset to manage",[r["dataset_type"] for r in rows],key="manage_entity")
                row=next(r for r in rows if r["dataset_type"]==entity)
                q=row.get("quality") or {}; a,b,c=st.columns(3)
                with a:kpi("Records",f'{row.get("row_count",0):,}')
                with b:kpi("Quality",f'{q.get("score",0)}%')
                with c:kpi("Columns",str(len(row.get("columns") or [])))
                if st.button(f"Delete {entity} dataset",type="secondary"):
                    st.session_state.store.delete_dataset(st.session_state.user_id,entity); st.success(f"{entity} dataset deleted."); st.rerun()
            else: st.info("No datasets uploaded yet. Use Upload / Update to add your first dataset.")
        else:
            for entity,df in data.items():
                q=data_quality(df) if not df.empty else {"records":0,"score":0}
                st.markdown(f"**{entity.title()}** · {q.get('records',0):,} records")
    with t2:
        entity=st.selectbox("Dataset type",["customers","campaigns","interactions","sustainability","transactions"])
        uploaded=st.file_uploader("Upload CSV",type=["csv"],key="dataset_upload")
        if uploaded:
            try:
                new_df=process_upload(entity,uploaded); schema=schema_report(entity,new_df); q=data_quality(new_df)
                if not schema["valid"]: st.warning(f"Missing recommended required columns: {', '.join(schema['missing_required'])}. The file can still be stored, but some analytics may remain unavailable.")
                st.success(f"{entity} validated. {len(new_df):,} rows detected.")
                a,b,c,d=st.columns(4)
                with a:kpi("Quality",f'{q["score"]}%')
                with b:kpi("Records",f'{q["records"]:,}')
                with c:kpi("Missing",f'{q["missing_pct"]:.1f}%')
                with d:kpi("Duplicates",f'{q["duplicate_pct"]:.1f}%')
                st.dataframe(new_df.head(20),use_container_width=True,hide_index=True)
                if st.button(f"Save / Replace {entity}",type="primary"):
                    if st.session_state.get("mode")=="demo":
                        st.session_state.demo_data[entity]=new_df; st.success(f"Demo {entity} dataset replaced for this session."); st.rerun()
                    elif st.session_state.get("store"):
                        st.session_state.store.upsert_dataset(st.session_state.user_id,entity,uploaded.name,new_df,q); st.session_state.store.log_event(st.session_state.user_id,"dataset_upsert",entity,{"rows":len(new_df)}); st.success(f"{entity} dataset saved and active across Akensya analytics."); st.rerun()
                    else: st.error("Secure persistence is not configured. Add Supabase secrets first.")
            except Exception as e: st.error(str(e))
    with t3:
        st.info("API connectors are intentionally scaffolded. Your uploaded CSVs are already persistent for registered accounts; APIs can be added later without changing the analytics contract.")
        st.write("Planned: Google Analytics 4 · Google Ads · Meta Ads · Salesforce · HubSpot · Shopify")

elif page=="Descriptive Analytics":
    topbar("Descriptive Analytics","Understand what happened across campaigns, channels and customers.")
    k=executive_kpis(data); cols=st.columns(4)
    for col,pair in zip(cols,[("Revenue",money(k["revenue"])),("Spend",money(k["spend"])),("ROAS",f'{k["roas"]:.2f}x'),("Conversions",f'{k["conversions"]:,}')]):
        with col:kpi(*pair)
    ch=channel_performance(data.get("campaigns",pd.DataFrame()))
    if not ch.empty:
        st.markdown('<div class="section">Channel performance</div>',unsafe_allow_html=True); st.dataframe(ch,use_container_width=True,hide_index=True); st.bar_chart(ch.set_index("channel")["revenue"])
    else: st.info("Upload a campaigns dataset to populate channel analytics.")

elif page=="Predictive Analytics":
    topbar("Predictive Analytics","Estimate what is likely to happen next from your active data.")
    t1,t2,t3=st.tabs(["Revenue Forecast","Churn Prediction","Model Notes"])
    with t1:
        fc=revenue_forecast(data.get("transactions",pd.DataFrame()))
        if not fc.empty:
            st.line_chart(fc.set_index("date")[["actual","forecast"]])
            future=fc[fc["actual"].isna()]["forecast"].dropna()
            a,b,c=st.columns(3)
            with a:kpi("Next forecast",money(future.iloc[0]) if len(future) else "—")
            with b:kpi("Forecast horizon",f'{len(future)} days')
            with c:kpi("Method","Trend regression")
            st.dataframe(fc.tail(21),use_container_width=True,hide_index=True)
        else: st.warning("Revenue Forecast needs a transactions dataset with date and amount columns.")
    with t2:
        churn=churn_predictions(data)
        if not churn.empty:
            a,b,c=st.columns(3)
            with a:kpi("High Risk",f'{(churn.risk_band.astype(str)=="High").sum():,}')
            with b:kpi("Medium Risk",f'{(churn.risk_band.astype(str)=="Medium").sum():,}')
            with c:kpi("Low Risk",f'{(churn.risk_band.astype(str)=="Low").sum():,}')
            st.dataframe(churn.sort_values("churn_probability",ascending=False),use_container_width=True,hide_index=True)
        else: st.warning("Churn Prediction needs customers and transactions data.")
    with t3:
        st.markdown("**Revenue Forecast** · Linear trend regression over daily revenue when enough history is available; rolling mean fallback for short histories.")
        st.markdown("**Churn Prediction** · Behavioral recency-risk proxy in the MVP because most marketing CSVs do not contain a supervised churn label. A trained classifier can replace this from Colab later.")
        st.markdown("**CLV Prediction** · Transaction value + order-frequency model with historical CLV floor when available.")
        st.markdown("**Important** · Predictions are directional estimates, not guarantees. Model performance should be evaluated after a sufficiently large labeled dataset is connected.")

elif page=="Prescriptive Analytics":
    topbar("Prescriptive Analytics","Move from prediction to the next-best action.")
    recs=build_recommendations(data)
    if recs.empty: st.info("Upload campaign/customer data to generate recommendations.")
    for _,r in recs.iterrows():
        st.markdown(f'<div class="action"><strong>{r["priority"]} · {r["title"]}</strong><br>{r["reason"]}<br><b>Expected impact:</b> {r["impact"]}</div><br>',unsafe_allow_html=True)
        if st.button("Review",key="review_"+str(r["id"])): st.success("Recommendation marked for review.")

elif page=="Customer Intelligence":
    topbar("Customer Intelligence","Understand who your customers are and where value is created.")
    st.write("Use the submenu in the sidebar for Journey, Segmentation and CLV Prediction.")
    seg=customer_segments(data.get("customers",pd.DataFrame()))
    if not seg.empty: st.dataframe(seg,use_container_width=True,hide_index=True)
    else: st.info("Upload a customers dataset with customer_id and lifetime_value to populate Customer Intelligence.")

elif page=="Customer Journey":
    topbar("Customer Journey","Identify the largest drop-offs from awareness to loyalty.")
    f=journey_funnel(data.get("interactions",pd.DataFrame()))
    if not f.empty: st.bar_chart(f.set_index("stage")["customers"]); st.dataframe(f,use_container_width=True,hide_index=True)
    else: st.info("Upload interactions data with customer_id and stage.")

elif page=="Customer Segmentation":
    topbar("Customer Segmentation","Group customers by observable value and engagement characteristics.")
    seg=customer_segments(data.get("customers",pd.DataFrame()))
    if not seg.empty: st.dataframe(seg,use_container_width=True,hide_index=True); st.bar_chart(seg.set_index("segment")["customers"])
    else: st.info("Upload customers data with lifetime_value.")

elif page=="CLV Prediction":
    topbar("CLV Prediction","Estimate customer value to prioritize retention and growth.")
    clv=clv_predictions(data)
    if not clv.empty:
        a,b,c=st.columns(3)
        with a:kpi("Average CLV",money(clv.predicted_clv.mean()))
        with b:kpi("90th percentile",money(clv.predicted_clv.quantile(.9)))
        with c:kpi("Customers",f'{len(clv):,}')
        st.dataframe(clv.sort_values("predicted_clv",ascending=False),use_container_width=True,hide_index=True)
        st.bar_chart(clv.head(20).set_index("customer_id")["predicted_clv"])
    else: st.info("Upload customers and transactions datasets to calculate CLV.")

elif page=="Campaign Intelligence":
    topbar("Campaign Intelligence","Compare campaign economics and identify optimization opportunities.")
    ct=campaign_table(data.get("campaigns",pd.DataFrame()))
    if not ct.empty:
        st.dataframe(ct,use_container_width=True,hide_index=True)
        if "campaign_name" in ct:
            campaign=st.selectbox("Select campaign",ct["campaign_name"].tolist()); row=ct[ct.campaign_name==campaign].iloc[0]
            a,b,c,d=st.columns(4)
            with a:kpi("Spend",money(row.get("spend",0)))
            with b:kpi("Revenue",money(row.get("revenue",0)))
            with c:kpi("ROAS",f'{float(row.get("roas",0)):.2f}x')
            with d:kpi("Conversion",f'{float(row.get("conversion_rate",0)):.1%}')
    else: st.info("Upload campaigns data to populate Campaign Intelligence.")

elif page=="Sustainability":
    topbar("Green Intelligence™","Track estimated marketing impact alongside commercial performance.")
    s=sustainability_score(data); a,b,c=st.columns(3)
    with a:kpi("Green Score",f'{s["score"]}/100',"Illustrative estimate")
    with b:kpi("Estimated emissions",f'{s["emissions"]:.0f} kg',"Sample assumption")
    with c:kpi("Estimated reach",f'{s["reach"]:,}')
    sus=data.get("sustainability",pd.DataFrame())
    if not sus.empty and {"channel","estimated_emissions"}.issubset(sus.columns): st.bar_chart(sus.groupby("channel")["estimated_emissions"].mean())
    st.warning("Sustainability metrics in this academic prototype are illustrative estimates, not verified environmental measurements.")
    st.markdown(f'<div class="insight"><b>Green Recommendation</b><br>{s["recommendation"]}</div>',unsafe_allow_html=True)

elif page=="Ask Akensya":
    topbar("Ask Akensya","Ask questions about the active marketing dataset and get evidence-backed decision intelligence.")
    st.caption("Ask about revenue, forecasts, campaigns, ROAS, churn, CLV, segments, recommendations, journey or sustainability.")
    question=st.text_area("Ask Akensya anything...",placeholder="Why did our ROAS fall, which campaign should I optimise, and what should I do next?")
    if st.button("Ask Akensya",type="primary"):
        with st.spinner("Akensya is analysing your active data..."):
            answer=answer_question(question,data,st.session_state.get("company","your company"))
        st.markdown(f'<div class="insight"><b>AKENSYA</b><br>{answer}</div>',unsafe_allow_html=True)
        if os.getenv("OPENAI_API_KEY"): st.caption("Answer grounded in current application analytics with the configured AI model.")
        else: st.caption("Answer grounded in current application analytics. Add OPENAI_API_KEY in Streamlit Secrets to enable the optional natural-language model layer.")

elif page=="Settings":
    topbar("Settings","Account, data ownership and deployment configuration.")
    st.subheader("Account")
    st.write(f"**Company:** {st.session_state.get('company','My Brand')}")
    st.write(f"**Mode:** {'Demo' if st.session_state.get('mode')=='demo' else 'Registered account'}")
    if st.session_state.get("mode")=="user": st.write(f"**User ID:** `{st.session_state.get('user_id')}`")
    st.subheader("Data ownership")
    st.info("Registered account datasets are stored under the authenticated user ID and protected by Supabase Row Level Security. Demo data is kept in the demo workspace and is not mixed with registered accounts.")
    st.subheader("AI")
    st.write("Ask Akensya uses governed application analytics first. If OPENAI_API_KEY is configured, only a bounded evidence context is sent to the selected model for natural-language synthesis.")
    st.subheader("Deployment")
    st.code("Google Colab → experimentation\nGitHub → source of truth\nSupabase → auth + persistent tenant data\nStreamlit Cloud → always-on application")
    if st.button("Log out",type="secondary"):
        if st.session_state.get("store") and st.session_state.get("mode")=="user": st.session_state.store.sign_out()
        reset_runtime()
