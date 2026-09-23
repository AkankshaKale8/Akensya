# Akensya — AI Decision Intelligence SaaS Prototype

**Insights. Predict. Act.**

This is a responsive Streamlit prototype designed around the Akensya master workflow.

## Architecture

Google Colab → experimentation/training  
GitHub → permanent source + sample data + model artifacts  
Database/API layer → persistent application events/data  
Streamlit Community Cloud → always-on web application

**Google Colab is not required to remain open.**

## Modules

1. Authentication
2. Company Onboarding
3. Data Hub
4. Executive Dashboard
5. Descriptive Analytics
6. Predictive Analytics
7. Prescriptive Analytics
8. Customer Intelligence
9. Campaign Intelligence
10. Sustainability / Green Intelligence
11. Ask Akensya
12. Settings

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

Push the repository to GitHub and deploy `app.py` using Streamlit Community Cloud. The resulting HTTPS application can be opened from desktop and mobile browsers without running Colab.

## Persistence

The prototype includes a SQLite event store for local/demo persistence. For a real multi-tenant SaaS, use a managed PostgreSQL/Supabase database and store credentials in Streamlit secrets or the deployment platform's secret manager.

## API-ready design

Future sources should follow:

API → connector → normalization → database → analytics/model layer → UI

Planned connectors include GA4, Google Ads, Meta Ads, Salesforce, HubSpot and Shopify.

## Brand

The supplied Akensya logo is stored at `assets/akensya_logo.png` and used directly by the Streamlit UI. The interface palette is derived from the logo: deep navy, electric blue/cyan and purple/violet.
