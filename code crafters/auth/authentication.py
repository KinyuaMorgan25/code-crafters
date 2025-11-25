"""
Authentication logic for Streamlit.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional

import streamlit as st
from werkzeug.security import check_password_hash, generate_password_hash

from config import MAX_FINE_BEFORE_BLOCK
from database.database import run_query
from utils.validators import validate_email

SESSION_TIMEOUT_MINUTES = 60
SYNC_INTERVAL_SECONDS = 60


def _load_user(email: str) -> Optional[Dict]:
    return run_query(
        "SELECT * FROM users WHERE email = %s",
        (email,),
        fetch="one",
    )


def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """Validate credentials against the DB."""
    user = _load_user(email)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def register_user(full_name: str, email: str, password: str) -> Optional[Dict]:
    """Create a new user entry."""
    if not validate_email(email):
        st.warning("Please provide a valid email.")
        return None
    existing = _load_user(email)
    if existing:
        st.warning("An account with this email already exists.")
        return None

    password_hash = generate_password_hash(password, method="scrypt")
    run_query(
        """
        INSERT INTO users (full_name, email, password_hash, role, total_fines)
        VALUES (%s, %s, %s, 'user', 0.00)
        """,
        (full_name, email, password_hash),
        fetch="none",
    )
    return _load_user(email)


def create_session(user: Dict) -> None:
    st.session_state.authenticated = True
    st.session_state.user = {
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
        "total_fines": user.get("total_fines", 0.0),
    }
    st.session_state.last_active = datetime.utcnow()
    st.session_state.user_last_sync = datetime.utcnow()


def current_user() -> Optional[Dict]:
    """Return the active user if the session is still valid."""
    user = st.session_state.get("user")
    last_active = st.session_state.get("last_active")
    if not st.session_state.get("authenticated") or not user:
        return None
    if last_active and datetime.utcnow() - last_active > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        logout()
        return None
    if last_active and datetime.utcnow() - last_active > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        logout()
        return None
    st.session_state.last_active = datetime.utcnow()

    last_sync = st.session_state.get("user_last_sync")
    if (
        not last_sync
        or datetime.utcnow() - last_sync > timedelta(seconds=SYNC_INTERVAL_SECONDS)
    ):
        fresh = run_query(
            "SELECT full_name, email, role, total_fines FROM users WHERE user_id = %s",
            (user["user_id"],),
            fetch="one",
        )
        if fresh:
            st.session_state.user.update(fresh)
            st.session_state.user_last_sync = datetime.utcnow()
    return st.session_state.user


def require_role(*roles: str) -> bool:
    """Gate UI sections by role."""
    user = current_user()
    if not user or user["role"] not in roles:
        st.error("You do not have access to this section.")
        return False
    return True


def logout() -> None:
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.last_active = None
    st.session_state.user_last_sync = None


def can_borrow(user: Dict) -> bool:
    """Business rule: block if fines exceed threshold."""
    return user.get("total_fines", 0.0) <= MAX_FINE_BEFORE_BLOCK

