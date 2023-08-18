#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add module of the app.

Add a new book to the collection of books that you maintain.
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
    "https://assets6.lottiefiles.com/packages/lf20_hMl7FE.json"
)
st_lottie(lottie_add, speed=1, height=100, key="initial")

st.markdown(
    """
## Add a new book
Specify the book details below. Most details can be left empty and edited later on the update page.
The exceptions are the title and the author.
"""
)

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
    published_year = st.number_input("Published year", min_value=0, max_value=2023)
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
        "current_date": pd.Timestamp.today(),
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
        st.success("Books added!")
    else:
        st.warning("Book already exists")

st.markdown("### Edited books")
st.write(st.session_state.today_books_df)

if st.button("Save updates"):
    saved = st.session_state.bk.save_books(st.session_state.today_books_df)
    if saved:
        st.success("Books saved!")
        (
            st.session_state.books_df,
            st.session_state.today_books_df,
            st.session_state.latest_book_state_df,
        ) = st.session_state.bk.update_tables()
