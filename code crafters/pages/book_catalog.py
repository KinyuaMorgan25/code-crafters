"""
Book catalog UI.
"""

from __future__ import annotations

import streamlit as st

from auth.authentication import current_user
from config import Pagination
from utils.helpers import borrow_book, create_reservation, fetch_book_catalog, fetch_book_details


def _render_book_card(book: dict, user_id: int) -> None:
    with st.expander(f"{book['title']} — {book.get('category_name', 'Uncategorized')}", expanded=False):
        st.markdown(f"**ISBN:** {book['isbn']}")
        st.markdown(f"**Available copies:** {book['available_copies'] or 0}")
        details = fetch_book_details(book["book_id"])
        if details:
            st.write(details.get("description") or "No description available.")
            if details.get("authors"):
                st.caption(f"Authors: {details['authors']}")

        cols = st.columns(2)
        with cols[0]:
            if st.button("Borrow", key=f"borrow_{book['book_id']}"):
                success, message = borrow_book(user_id, book["book_id"])
                (st.success if success else st.error)(message)
                if success:
                    st.experimental_rerun()
        with cols[1]:
            if st.button("Reserve", key=f"reserve_{book['book_id']}"):
                success, message = create_reservation(user_id, book["book_id"])
                (st.success if success else st.warning)(message)


def render_book_catalog() -> None:
    st.header("Book Catalog")
    user = current_user()
    if not user:
        st.info("Please sign in to view the catalog.")
        return

    if "catalog_page" not in st.session_state:
        st.session_state.catalog_page = 1
    if "catalog_search" not in st.session_state:
        st.session_state.catalog_search = ""

    with st.form("catalog_filters"):
        search = st.text_input("Search by title or ISBN", value=st.session_state.catalog_search)
        page_size = st.selectbox("Results per page", options=[5, 10, 15, 20], index=1)
        submitted = st.form_submit_button("Apply")
    if submitted:
        st.session_state.catalog_search = search
        st.session_state.catalog_page = 1

    pagination = Pagination(page=st.session_state.catalog_page, page_size=page_size)
    books = fetch_book_catalog(
        search=st.session_state.catalog_search.strip() or None,
        pagination=pagination,
    )
    if not books:
        st.warning("No books found. Try adjusting your filters.")
        return

    for book in books:
        _render_book_card(book, user["user_id"])

    cols = st.columns(2)
    with cols[0]:
        if st.button("Previous") and st.session_state.catalog_page > 1:
            st.session_state.catalog_page -= 1
            st.experimental_rerun()
    with cols[1]:
        if st.button("Next") and len(books) == page_size:
            st.session_state.catalog_page += 1
            st.experimental_rerun()

