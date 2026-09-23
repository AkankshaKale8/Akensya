from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Optional
import pandas as pd
from io import StringIO

try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = object

class SupabaseStore:
    def __init__(self, url: str, key: str):
        if not url or not key or create_client is None:
            raise RuntimeError("Supabase configuration is missing or the supabase package is unavailable.")
        self.client: Client = create_client(url, key)

    def set_session(self, access_token: str, refresh_token: str):
        if access_token and refresh_token:
            self.client.auth.set_session(access_token, refresh_token)

    def sign_in(self, email: str, password: str):
        return self.client.auth.sign_in_with_password({"email": email, "password": password})

    def sign_up(self, email: str, password: str, company_name: str):
        return self.client.auth.sign_up({"email": email, "password": password, "options": {"data": {"company_name": company_name}}})

    def sign_out(self):
        try:
            self.client.auth.sign_out()
        except Exception:
            pass

    def profile(self, user_id: str):
        r = self.client.table("profiles").select("id,company_name,industry,company_size,goals,stack").eq("id", user_id).maybe_single().execute()
        return r.data or {}

    def upsert_profile(self, user_id: str, payload: dict):
        row = {"id": user_id, **payload}
        return self.client.table("profiles").upsert(row).execute()

    def list_datasets(self, user_id: str):
        r = self.client.table("datasets").select("id,dataset_type,file_name,row_count,columns,quality,created_at,updated_at").eq("user_id", user_id).order("updated_at", desc=True).execute()
        return r.data or []

    def get_datasets(self, user_id: str):
        r = self.client.table("datasets").select("id,dataset_type,file_name,content,row_count,columns,quality,created_at,updated_at").eq("user_id", user_id).execute()
        result = {}
        for row in (r.data or []):
            try:
                result[row["dataset_type"]] = pd.read_csv(StringIO(row["content"]))
            except Exception:
                result[row["dataset_type"]] = pd.DataFrame()
        return result

    def upsert_dataset(self, user_id: str, entity: str, filename: str, df: pd.DataFrame, quality: dict):
        content = df.to_csv(index=False)
        payload = {
            "user_id": user_id,
            "dataset_type": entity,
            "file_name": filename,
            "content": content,
            "row_count": int(len(df)),
            "columns": list(df.columns),
            "quality": quality,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.client.table("datasets").upsert(payload, on_conflict="user_id,dataset_type").execute()

    def delete_dataset(self, user_id: str, entity: str):
        return self.client.table("datasets").delete().eq("user_id", user_id).eq("dataset_type", entity).execute()

    def log_event(self, user_id: Optional[str], event_type: str, entity: str, payload: dict):
        row = {"user_id": user_id, "event_type": event_type, "entity": entity, "payload": payload}
        try:
            self.client.table("events").insert(row).execute()
        except Exception:
            pass


def make_store(st):
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_ANON_KEY")
    except Exception:
        url = key = None
    if url and key:
        return SupabaseStore(url, key)
    return None
