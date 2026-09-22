# Akensya deployment — secure multi-brand setup

## 1. Supabase
Create a project and open SQL Editor. Run:

`database/supabase_schema.sql`

This creates:
- `profiles`
- `datasets`
- `events`
- Row Level Security policies
- signup profile trigger

## 2. Streamlit Cloud secrets
Add these in App → Settings → Secrets:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"
OPENAI_API_KEY = "OPTIONAL"
OPENAI_MODEL = "gpt-4o-mini"
```

If OpenAI is omitted, Ask Akensya still works with the built-in analytics reasoning engine.

## 3. GitHub
Replace the project files with this package. Do not upload `.pyc`, `__pycache__`, database files or secrets.

## 4. Streamlit
Deploy `app.py`.

## 5. Security behavior
- Demo mode uses only local demo CSVs.
- Registered accounts authenticate through Supabase Auth.
- Every dataset row has `user_id`.
- RLS allows users to select/insert/update/delete only their own datasets.
- The app does not expose service-role credentials.
- Ask Akensya uses only the active user's analytics context.

## 6. Dataset lifecycle
Upload → normalize → validate → save/replace → active analytics → update/replace or delete.

Deleting a dataset removes the stored dataset for that user and the analytics module will show a data requirement message until a replacement is uploaded.
