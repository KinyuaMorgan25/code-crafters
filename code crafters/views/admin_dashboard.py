"""
Admin dashboard UI.
"""

from __future__ import annotations

import streamlit as st

from auth.authentication import current_user, require_role
from config import Pagination
from database.database import run_query
from utils.helpers import (
    fetch_book_catalog,
    fetch_dashboard_metrics,
    return_book,
    update_fine_totals,
)


def _add_book_form():
    st.subheader("Add Book")
    with st.form("add_book"):
        title = st.text_input("Title")
        isbn = st.text_input("ISBN")
        description = st.text_area("Description")
        category_id = st.number_input("Category ID", min_value=1, step=1)
        submitted = st.form_submit_button("Create book")
    if submitted:
        run_query(
            """
            INSERT INTO books (title, isbn, description, category_id)
            VALUES (%s, %s, %s, %s)
            """,
            (title, isbn, description, int(category_id)),
            fetch="none",
        )
        st.success("Book created.")


def _add_copy_form():
    st.subheader("Add Copy")
    with st.form("add_copy"):
        book_id = st.number_input("Book ID", min_value=1, step=1)
        location = st.text_input("Shelf location", value="Main")
        submitted = st.form_submit_button("Create copy")
    if submitted:
        run_query(
            "INSERT INTO book_copies (book_id, status, location) VALUES (%s, 'available', %s)",
            (int(book_id), location),
            fetch="none",
        )
        st.success("Copy added.")


def _user_table():
    st.subheader("Users")
    users = run_query(
        "SELECT user_id, full_name, email, role, total_fines FROM users ORDER BY created_at DESC LIMIT 50"
    )
    st.dataframe(users, use_container_width=True)


def _reports():
    st.subheader("Most Borrowed Books")
    top_books = run_query(
        """
        SELECT b.title, COUNT(*) AS times_borrowed
        FROM borrow_transactions bt
        JOIN book_copies bc ON bc.copy_id = bt.copy_id
        JOIN books b ON b.book_id = bc.book_id
        GROUP BY b.book_id
        ORDER BY times_borrowed DESC
        LIMIT 10
        """
    )
    if top_books:
        st.dataframe(top_books, use_container_width=True)
    else:
        st.info("No transactions yet.")

    st.subheader("Overdue Transactions")
    overdue = run_query(
        """
        SELECT bt.transaction_id, u.full_name, b.title, bt.due_date, bt.fine_amount
        FROM borrow_transactions bt
        JOIN users u ON u.user_id = bt.user_id
        JOIN book_copies bc ON bc.copy_id = bt.copy_id
        JOIN books b ON b.book_id = bc.book_id
        WHERE bt.status = 'overdue'
        LIMIT 20
        """
    )
    if overdue:
        st.dataframe(overdue, use_container_width=True)
    else:
        st.success("No overdue transactions 🎉")


def render_admin_dashboard() -> None:
    user = current_user()
    if not user or not require_role("admin"):
        return

    st.header("Admin Panel")
    metrics = fetch_dashboard_metrics()
    cols = st.columns(4)
    cols[0].metric("Active Loans", metrics["active_loans"])
    cols[1].metric("Overdue", metrics["overdue"])
    cols[2].metric("Reservations", metrics["reservations"])
    cols[3].metric("Total fines", f"${metrics['fines']:.2f}")

    tabs = st.tabs(["Books", "Users", "Transactions", "Reports"])

    with tabs[0]:
        _add_book_form()
        _add_copy_form()
        st.subheader("Inventory Snapshot")
        books = fetch_book_catalog(pagination=Pagination(page_size=10))
        st.dataframe(books, use_container_width=True)

    with tabs[1]:
        _user_table()

    with tabs[2]:
        st.subheader("Process Return")
        with st.form("process_return"):
            transaction_id = st.number_input("Transaction ID", min_value=1, step=1)
            submitted = st.form_submit_button("Mark as returned")
        if submitted:
            success, message = return_book(int(transaction_id))
            if success:
                st.success(message)
            else:
                st.error(message)

        if st.button("Recalculate fines"):
            update_fine_totals()
            st.info("Fine calculation triggered.")

    with tabs[3]:
        _reports()

