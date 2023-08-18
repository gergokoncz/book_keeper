#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Filter module of the app.

Filter and look at related books,
narrow by various categories,
look at aggregate statistics.
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
    "https://lottie.host/3dc97927-4cb1-433f-a03d-9bb218d0dfa5/1EfLbynHQa.json"
)
st_lottie(lottie_add, speed=1, height=100, key="initial")

st.markdown(
    """
## Filter books
Filter books by topic, publisher, author, published date and others...
"""
)
