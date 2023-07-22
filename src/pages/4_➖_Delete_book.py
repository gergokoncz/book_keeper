#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
from streamlit_lottie import st_lottie
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

selected_slug = st.selectbox(
    "Select book", st.session_state.latest_book_state_df["slug"].unique()
)

if st.button("Delete book"):
    success, st.session_state.today_books_df = st.session_state.bk.delete_book(
        selected_slug,
        st.session_state.today_books_df,
        st.session_state.latest_book_state_df,
    )
    if success:
        st.success("Books updated!")
    else:
        st.error("Something went wrong, please try again.")
