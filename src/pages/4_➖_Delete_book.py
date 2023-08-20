#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Delete module of the app.

Delete a book from the collection of books that you maintain.
Also revert the deletion on the day you have done it.
"""

from os import environ

import pandas as pd
import streamlit as st
from streamlit_lottie import st_lottie

from utils import BookKeeperIO, load_lottie_url

st.set_page_config(layout="wide")

if "bk" not in st.session_state:
    bucket = environ.get("BOOKSTORAGE_BUCKET")
    st.session_state.bk = BookKeeperIO("gergokoncz", bucket=bucket)

# get an update on the tables
if "books_df" not in st.session_state:
    (
        st.session_state.books_df,
        st.session_state.today_books_df,
        st.session_state.latest_book_state_df,
    ) = st.session_state.bk.update_tables()

lottie_add = load_lottie_url(
    "https://assets7.lottiefiles.com/packages/lf20_nux6g0kx.json"
)
st_lottie(lottie_add, speed=1, height=100, key="initial")

st.markdown(
    """
## Delete existing book
Select the book by slug and confirm delete.
"""
)

selected_slug_for_deletion = st.selectbox(
    "Select book",
    st.session_state.bk.remove_deleted_books(st.session_state.latest_book_state_df)[
        "slug"
    ].unique(),
)

if st.button("Delete book"):
    success, st.session_state.today_books_df = st.session_state.bk.delete_book(
        selected_slug_for_deletion,
        st.session_state.today_books_df,
        st.session_state.latest_book_state_df,
    )
    if success:
        saved = st.session_state.bk.save_books(st.session_state.today_books_df)
        if saved:
            st.success("Book deleted!")
            (
                st.session_state.books_df,
                st.session_state.today_books_df,
                st.session_state.latest_book_state_df,
            ) = st.session_state.bk.update_tables()
        else:
            st.error("Something went wrong, please try again.")
    else:
        st.error("Something went wrong, please try again.")

st.markdown(
    """
## Revert deletion of book
Select slug from deleted books and revert deletion - can only be done on the same day deletion took place.
"""
)


today_books_df = st.session_state.today_books_df
deleted_books_df = today_books_df.query("deleted==True")

selected_slug_for_revert = st.selectbox(
    "Select book", deleted_books_df["slug"].unique()
)

if st.button("Revert deletion"):
    success, st.session_state.today_books_df = st.session_state.bk.revert_deletion_book(
        selected_slug_for_revert,
        st.session_state.today_books_df,
        st.session_state.latest_book_state_df,
    )
    if success:
        saved = st.session_state.bk.save_books(st.session_state.today_books_df)
        if saved:
            st.success("Book deletion reverted!")
            (
                st.session_state.books_df,
                st.session_state.today_books_df,
                st.session_state.latest_book_state_df,
            ) = st.session_state.bk.update_tables()
        else:
            st.error("Something went wrong, please try again.")
    else:
        st.error("Something went wrong, please try again.")
