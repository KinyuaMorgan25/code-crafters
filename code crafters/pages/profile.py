"""
User profile page.
"""

from __future__ import annotations

import streamlit as st

from auth.authentication import current_user, logout
from utils.helpers import fetch_user_transactions


def render_profile_page() -> None:
    user = current_user()
    if not user:
        st.info("Please sign in to access your profile.")
        return

    st.header("Profile")
    st.write(f"**Name:** {user['full_name']}")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Role:** {user['role'].title()}")
    st.write(f"**Outstanding fines:** ${user.get('total_fines', 0.0):.2f}")

    if st.button("Sign out"):
        logout()
        st.experimental_rerun()

    st.subheader("Borrowing History")
    transactions = fetch_user_transactions(user["user_id"])
    if transactions:
        st.dataframe(transactions, use_container_width=True)
    else:
        st.info("No transactions yet.")

