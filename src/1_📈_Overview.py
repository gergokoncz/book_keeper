#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is the entry point for BookKeeper app.

Showing some basic statistics of the books that you have logged.
"""

from os import environ

import altair as alt
import streamlit as st
from streamlit_lottie import st_lottie

from utils import BookKeeperDataOps, BookKeeperIO, load_lottie_url

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


lottie_books = load_lottie_url(
    "https://assets3.lottiefiles.com/packages/lf20_4XmSkB.json"
)
st_lottie(lottie_books, speed=1, height=100, key="initial")

st.title("BookKeeper")

st.markdown("A simple app to keep track of the books you read and you plan to read.")

st.markdown("## Your stats")

st.write(
    st.session_state.bk.remove_deleted_books(st.session_state.latest_book_state_df)
)

bkdata = BookKeeperDataOps(
    st.session_state.bk.remove_deleted_books(st.session_state.books_df)
)
latest_books_df = bkdata.add_books_state(
    st.session_state.bk.remove_deleted_books(st.session_state.latest_book_state_df)
)
st.write(latest_books_df)

fig = alt.Chart(latest_books_df).mark_bar().encode(x="state", y="count()")
st.altair_chart(fig, use_container_width=True)
