#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Search module of the app.

Search your books by name and see event log for them.
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
    "https://lottie.host/4b6cf1c6-5ba6-4d4e-896f-64121f952847/sZlE6SNKZf.json"
)
st_lottie(lottie_add, speed=1, height=100, key="initial")

st.markdown(
    """
## Search for a book
Search for a book by title or author (slug),
and see what updates have been added to it.
"""
)
