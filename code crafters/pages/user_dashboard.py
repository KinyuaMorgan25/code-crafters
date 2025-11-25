"""
Member dashboard UI.
"""

from __future__ import annotations

import streamlit as st

from auth.authentication import current_user
from utils.helpers import fetch_active_loans, fetch_dashboard_metrics


def render_user_dashboard() -> None:
    user = current_user()
    if not user:
        st.info("Sign in to access your dashboard.")
        return

    st.header(f"Welcome, {user['full_name']}")

    metrics = fetch_dashboard_metrics()
    cols = st.columns(4)
    cols[0].metric("Active Loans", metrics["active_loans"])
    cols[1].metric("Overdue", metrics["overdue"])
    cols[2].metric("Reservations", metrics["reservations"])
    cols[3].metric("Fines (USD)", f"${metrics['fines']:.2f}")

    st.subheader("Your Active Loans")
    loans = fetch_active_loans(user["user_id"])
    if loans:
        st.dataframe(loans, use_container_width=True)
    else:
        st.info("You have no active loans.")

