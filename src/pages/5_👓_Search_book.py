#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Search module of the app.

Search your books by name and see event log for them.
"""

import streamlit as st

from utils import BookKeeperDataOps, authenticated_with_data

# GLOBALS
SEARCH_LOTTIE_URL = (
    "https://lottie.host/4b6cf1c6-5ba6-4d4e-896f-64121f952847/sZlE6SNKZf.json"
)


@authenticated_with_data(
    lottie_url=SEARCH_LOTTIE_URL,
    title="Search for books",
    description="Filter books by properties, or search for a book by title and get the detailed logs and see its history.",
)
def main() -> None:
    """Main flow of the Search page."""
    bk_data_ops = BookKeeperDataOps()

    not_deleted_books_latest_state = st.session_state.latest_book_state_df.query(
        "deleted==False"
    )

    # define filters

    # filter by author

    st.markdown("### Configure the filters to find subset of books")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_author = st.multiselect(
            "Select author", not_deleted_books_latest_state["author"].unique()
        )

        selected_publisher = st.multiselect(
            "Select publisher",
            not_deleted_books_latest_state["publisher"].unique(),
        )

    with col2:
        min_published_year: int = not_deleted_books_latest_state["published_year"].min()
        max_published_year: int = not_deleted_books_latest_state["published_year"].max()

        selected_min_published_year = st.number_input(
            "Minimum published year",
            min_published_year,
            max_published_year,
            min_published_year,
        )

        selected_max_published_year = st.number_input(
            "Maximum published year",
            min_published_year,
            max_published_year,
            max_published_year,
        )

    filtered_books = bk_data_ops.filter_books(
        st.session_state.latest_book_state_df,
        selected_author,
        selected_min_published_year,
        selected_max_published_year,
        selected_publisher,
    )
    st.markdown("Books matching filters")
    st.write(bk_data_ops.show_books_overview(filtered_books))

    # filter by published year

    # filter by tag

    st.divider()
    st.markdown("### Select slug for book and find detailed logs")

    selected_slug = st.selectbox(  # noqa: F841
        "Select book", not_deleted_books_latest_state["slug"].unique()
    )

    # get the book
    selected_book_df = bk_data_ops.get_logs_for_book(
        st.session_state.books_df, selected_slug
    )
    st.write(selected_book_df.sort_values("log_created_at", ascending=True))


if __name__ == "__main__":
    main()
