from __future__ import annotations

import streamlit as st


def _client():
    from supabase import create_client
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def supabase_configured() -> bool:
    try:
        return _client() is not None
    except Exception:
        return False


def _set_session(auth_response):
    session = getattr(auth_response, "session", None)
    user = getattr(auth_response, "user", None)
    if session:
        st.session_state.access_token = session.access_token
        st.session_state.refresh_token = session.refresh_token
    if user:
        st.session_state.user_id = user.id
        st.session_state.user_email = user.email or ""
    st.session_state.authenticated = bool(user)


def sign_in(email: str, password: str):
    client = _client()
    if client is None:
        return False, "Supabase is not configured. Add SUPABASE_URL and SUPABASE_KEY to Streamlit Secrets."

    try:
        response = client.auth.sign_in_with_password({
            "email": email.strip().lower(),
            "password": password,
        })
        _set_session(response)
        return True, "Login successful."
    except Exception as exc:
        return False, str(exc)


def sign_up(email: str, password: str, company: str):
    client = _client()
    if client is None:
        return False, "Supabase is not configured. Add SUPABASE_URL and SUPABASE_KEY to Streamlit Secrets."

    try:
        response = client.auth.sign_up({
            "email": email.strip().lower(),
            "password": password,
            "options": {"data": {"company": company.strip()}},
        })

        # Depending on Supabase email-confirmation settings, a session may or may not be returned.
        if getattr(response, "user", None):
            user = response.user
            st.session_state.user_id = user.id
            st.session_state.user_email = user.email or email.strip().lower()
        if getattr(response, "session", None):
            _set_session(response)
        return True, "Account created. Check your email if confirmation is enabled, then log in."
    except Exception as exc:
        return False, str(exc)


def sign_out():
    client = _client()
    try:
        if client is not None:
            client.auth.sign_out()
    except Exception:
        pass

    for key in [
        "authenticated", "user_id", "user_email", "access_token",
        "refresh_token", "company", "user_company", "data",
    ]:
        st.session_state.pop(key, None)

    st.session_state.authenticated = False
    st.session_state.company = "DemoBrand"


def restore_session() -> bool:
    client = _client()
    if client is None:
        return False

    try:
        session = client.auth.get_session()
        if session and session.user:
            st.session_state.authenticated = True
            st.session_state.user_id = session.user.id
            st.session_state.user_email = session.user.email or ""
            st.session_state.access_token = session.access_token
            st.session_state.refresh_token = session.refresh_token
            return True
    except Exception:
        return False
    return False


def demo_login(email: str, password: str) -> bool:
    demo_email = st.secrets.get("DEMO_EMAIL", "demo@akensya.ai")
    demo_password = st.secrets.get("DEMO_PASSWORD", "Akensya@123")
    if email.strip().lower() == demo_email.lower() and password == demo_password:
        st.session_state.authenticated = True
        st.session_state.user_id = "demo"
        st.session_state.user_email = demo_email
        st.session_state.company = "DemoBrand"
        st.session_state.user_company = "DemoBrand"
        st.session_state.demo_mode = True
        return True
    return False
