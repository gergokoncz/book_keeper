#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add module of the app.

Add a new book to the collection of books that you maintain.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from utils import base_layout, with_authentication, with_user_logs

# VARS
ADD_LOTTIE_URL = "https://assets6.lottiefiles.com/packages/lf20_hMl7FE.json"


@base_layout(
    lottie_url=ADD_LOTTIE_URL,
    title="Add a new book",
    description="Specify the book details below. Most details can be left empty and edited later on the update page. The exceptions are the title and the author.",
)
@with_authentication
@with_user_logs
def main() -> None:
    """Main flow of the Add page."""
    finished = st.checkbox("Finished")
    finish_date = None

    col1, col2, col3 = st.columns(3)

    with col1:
        book_title = st.text_input("Title")
        book_subtitle = st.text_input("Subtitle")
        book_author = st.text_input("Author")
        book_publisher = st.text_input("Publisher")
        if finished:
            finish_date = st.date_input("Finish date", value=None)

    with col2:
        published_year = st.number_input(
            "Published year",
            min_value=0,
            max_value=datetime.now().year,
            value=datetime.now().year,
        )
        book_location = st.text_input("Location - physical or virtual")
        book_pageN = st.number_input(
            "Number of pages", min_value=0, max_value=100_000, value=100
        )
        book_pageCurrent = st.number_input(
            "Current page", min_value=0, max_value=100_000, value=0
        )

    with col3:
        book_tag1 = st.text_input("Tag1")
        # book_tag1 = st.multiselect("Tag1", st.session_state.books_df["tag1"].unique())
        book_tag2 = st.text_input("Tag2")
        book_tag3 = st.text_input("Tag3")
        book_language = st.selectbox(
            "Language", ["en", "hu", "de", "fr", "es", "it", "other"]
        )

    if st.button("Add book"):
        book = {
            "title": book_title,
            "subtitle": book_subtitle,
            "author": book_author,
            "location": book_location,
            "publisher": book_publisher,
            "published_year": published_year,
            "page_n": book_pageN,
            "page_current": book_pageCurrent,
            "log_created_at": pd.Timestamp.today(),
            "finish_date": finish_date,
            "tag1": book_tag1,
            "tag2": book_tag2,
            "tag3": book_tag3,
            "language": book_language,
        }
        success, st.session_state.today_books_df = st.session_state.bk.add_book(
            book, finished, st.session_state.today_books_df
        )

        if success:
            st.success("Book added!")
        else:
            st.warning("Book already exists")

    st.divider()

    # show edited and deleted books
    today_books_df = st.session_state.today_books_df
    edited_books_df = today_books_df.query("deleted==False")
    deleted_books_df = today_books_df.query("deleted==True")

    if not edited_books_df.empty:
        st.markdown("### Edited books - today")
        st.write(edited_books_df)

    if not deleted_books_df.empty:
        st.markdown("### Deleted books (today)")
        st.write(deleted_books_df)

    if not today_books_df.empty:
        if st.button("Save updates"):
            saved = st.session_state.bk.save_books(st.session_state.today_books_df)
            if saved:
                st.success("Books saved!")
                with st.spinner("Updating books..."):
                    (
                        st.session_state.books_df,
                        st.session_state.today_books_df,
                        st.session_state.latest_book_state_df,
                    ) = st.session_state.bk.get_updated_tables()


if __name__ == "__main__":
    main()
