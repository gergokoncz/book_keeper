#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
from os import environ

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

st.markdown(
    """
## Delete existing book
Select the book by slug and confirm delete.
"""
)

selected_slug = st.selectbox(
    "Select book", st.session_state.latest_book_state_df["slug"].unique()
)

if st.button("Delete book"):
    success, st.session_state.today_books_df = st.session_state.bk.delete_book(
        selected_slug, st.session_state.today_books_df
    )
    if success:
        st.success("Books updated!")
    else:
        st.error("Something went wrong, please try again.")