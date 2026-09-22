# Akensya — AI Decision Intelligence SaaS

A Streamlit SaaS prototype for marketing decision intelligence: descriptive analytics, predictive analytics, prescriptive actions, customer intelligence, campaign intelligence, sustainability and Ask Akensya.

## What's new in this version
- Secure Login / Create Account / Logout through Supabase Auth.
- Separate Demo workspace with isolated built-in sample data.
- User/brand-level dataset ownership with Supabase Row Level Security.
- Upload, replace/update and delete CSV datasets.
- Analytics dynamically consume the active user's datasets.
- Revenue Forecast, Churn Prediction and Model Notes are implemented and schema-aware.
- Ask Akensya combines deterministic analytics with an optional LLM layer.
- Existing navigation and Akensya visual system are preserved.

## Data model
Supported dataset types:
- customers
- campaigns
- interactions
- sustainability
- transactions

The upload normalizer accepts common aliases such as `customerid`, `clv`, `ltv`, `sales`, `revenue`, `cost`, `carbon`, etc.

## Deployment
1. Create a Supabase project.
2. Run `database/supabase_schema.sql` in Supabase SQL Editor.
3. In Streamlit Cloud, add secrets:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR_ANON_KEY"
OPENAI_API_KEY = "OPTIONAL"
OPENAI_MODEL = "gpt-4o-mini"
```

4. Deploy `app.py` from GitHub.
5. Create a real account or choose Demo.

Never commit secrets to GitHub.

## Colab
The notebooks remain experimentation assets. They are not required to keep the deployed Streamlit application online.
