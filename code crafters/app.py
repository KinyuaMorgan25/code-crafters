"""
Streamlit entry point for the Library Management System.
"""

from __future__ import annotations

import streamlit as st

from auth.authentication import (
    authenticate_user,
    create_session,
    current_user,
    logout,
    register_user,
)
from pages import (
    render_admin_dashboard,
    render_book_catalog,
    render_profile_page,
    render_user_dashboard,
)
from utils.validators import validate_password_strength


def _login_form():
    st.subheader("Sign in")
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        user = authenticate_user(email.strip(), password)
        if user:
            create_session(user)
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")


def _register_form():
    st.subheader("Create an account")
    with st.form("register_form"):
        full_name = st.text_input("Full name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Register")
    if submitted:
        if password != confirm:
            st.error("Passwords do not match.")
            return
        valid, message = validate_password_strength(password)
        if not valid:
            st.error(message)
            return
        user = register_user(full_name.strip(), email.strip(), password)
        if user:
            st.success("Account created. You can now sign in.")
        else:
            st.error("Unable to create account.")


def show_login_screen():
    st.title("Library Management System")
    tabs = st.tabs(["Login", "Register"])
    with tabs[0]:
        _login_form()
    with tabs[1]:
        _register_form()


def render_sidebar():
    user = current_user()
    st.sidebar.title("Navigation")
    options = ["Dashboard", "Catalog", "Profile"]
    if user and user["role"] == "admin":
        options.insert(1, "Admin")
    choice = st.sidebar.radio("Go to", options, key="nav_choice")
    if st.sidebar.button("Logout"):
        logout()
        st.experimental_rerun()
    return choice


def main():
    st.set_page_config(page_title="Library Management System", layout="wide")
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user = None

    if not st.session_state.authenticated:
        show_login_screen()
        return

    choice = render_sidebar()
    if choice == "Dashboard":
        render_user_dashboard()
    elif choice == "Catalog":
        render_book_catalog()
    elif choice == "Profile":
        render_profile_page()
    elif choice == "Admin":
        render_admin_dashboard()


if __name__ == "__main__":
    main()

