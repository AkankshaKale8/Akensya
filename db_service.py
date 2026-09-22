from __future__ import annotations

import datetime as dt
from typing import Dict, Optional

import streamlit as st

from services.data_service import dataframe_to_records, records_to_dataframe


DATASET_NAMES = ["customers", "campaigns", "interactions", "sustainability", "transactions"]


def _supabase():
    """Create a Supabase client from Streamlit secrets."""
    try:
        from supabase import create_client
    except ImportError:
        return None

    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def supabase_available() -> bool:
    return _supabase() is not None


def save_event(event_type: str, entity: str, payload: dict, user_id: Optional[str] = None):
    client = _supabase()
    if client is None:
        return False
    uid = user_id or st.session_state.get("user_id")
    if not uid:
        return False
    client.table("events").insert({
        "user_id": uid,
        "event_type": event_type,
        "entity": entity,
        "payload": payload,
        "created_at": dt.datetime.utcnow().isoformat(),
    }).execute()
    return True


def save_profile(user_id: str, email: str, company: str):
    client = _supabase()
    if client is None:
        return False
    client.table("profiles").upsert({
        "id": user_id,
        "email": email,
        "company": company,
        "updated_at": dt.datetime.utcnow().isoformat(),
    }).execute()
    return True


def save_dataset(user_id: str, entity: str, df):
    client = _supabase()
    if client is None:
        return False
    if entity not in DATASET_NAMES:
        raise ValueError(f"Unsupported dataset: {entity}")

    # Replace the user's dataset atomically at the application level.
    client.table("datasets").delete().eq("user_id", user_id).eq("dataset_name", entity).execute()

    rows = dataframe_to_records(df)
    batch_size = 500
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        payload = [
            {
                "user_id": user_id,
                "dataset_name": entity,
                "row_data": row,
            }
            for row in batch
        ]
        if payload:
            client.table("datasets").insert(payload).execute()

    save_event("dataset_saved", entity, {"rows": len(rows)}, user_id)
    return True


def replace_dataset(user_id: str, entity: str, df):
    return save_dataset(user_id, entity, df)


def load_dataset(user_id: str, entity: str):
    client = _supabase()
    if client is None:
        return None

    response = (
        client.table("datasets")
        .select("row_data")
        .eq("user_id", user_id)
        .eq("dataset_name", entity)
        .execute()
    )
    return records_to_dataframe([r["row_data"] for r in (response.data or [])])


def load_user_datasets(user_id: str) -> Dict:
    return {
        entity: load_dataset(user_id, entity)
        for entity in DATASET_NAMES
        if load_dataset(user_id, entity) is not None
    }


def delete_dataset(user_id: str, entity: str):
    client = _supabase()
    if client is None:
        return False
    client.table("datasets").delete().eq("user_id", user_id).eq("dataset_name", entity).execute()
    save_event("dataset_deleted", entity, {}, user_id)
    return True


def get_profile(user_id: str):
    client = _supabase()
    if client is None:
        return None
    response = client.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
    return response.data


def health_check():
    client = _supabase()
    if client is None:
        return False, "Supabase secrets or supabase-py are not configured."
    try:
        client.table("profiles").select("id").limit(1).execute()
        return True, "Supabase connection is active."
    except Exception as exc:
        return False, str(exc)
