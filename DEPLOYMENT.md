# Akensya — Always-On Deployment

## One-time deployment

1. Create a GitHub repository named `akensya-ai-decision-intelligence`.
2. Upload this entire folder.
3. Open Streamlit Community Cloud.
4. Connect the GitHub repository.
5. Select `app.py`.
6. Deploy.

## Runtime

After deployment:

GitHub → Streamlit Cloud → Akensya

Google Colab can be closed. It is only the AI/data laboratory.

## Production database

For true persistent SaaS data, configure PostgreSQL/Supabase and move `services/db_service.py` from the local SQLite fallback to the managed database.

## Secrets

Never commit API keys. Use Streamlit Cloud Secrets for:
- database URL
- LLM/API key
- Google credentials
- Meta credentials
- CRM credentials

## Mobile

The Streamlit layout is responsive and uses wide-screen containers that collapse naturally on mobile browsers. For a future native mobile experience, keep the same service/API layer and build a dedicated mobile client.
