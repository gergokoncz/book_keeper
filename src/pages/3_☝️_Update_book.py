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

lottie_books = load_lottie_url(
    "https://assets5.lottiefiles.com/packages/lf20_noyzw8ub.json"
)
st_lottie(lottie_books, speed=1, height=100, key="initial")


st.markdown(
    """
## Update existing book
Select book and update details the book.
"""
)

selected_slug = st.selectbox(
    "Select book", st.session_state.latest_book_state_df["slug"].unique()
)
selected_book = (
    st.session_state.latest_book_state_df.query("slug==@selected_slug")
    .iloc[0]
    .to_dict()
)

st.markdown("### Update book details")
finish_date = selected_book.get("finish_date")
finished = st.checkbox(
    "Finished",
    value=finish_date != pd.Timestamp("1990-01-01") and finish_date is not None,
)

title_col1, title_col2 = st.columns(2)

with title_col1:
    st.markdown(f"**Title**: {selected_book.get('title')}")

with title_col2:
    st.markdown(f"**Author**: {selected_book.get('author')}")


col1, col2, col3 = st.columns(3)

with col1:
    book_subtitle = st.text_input("Subtitle", value=selected_book.get("subtitle"))
    book_location = st.text_input(
        "Location - physical or virtual", value=selected_book.get("location")
    )
    book_publisher = st.text_input("Publisher", value=selected_book.get("publisher"))
    if finished:
        finish_date = st.date_input("Finish date", value=finish_date)

with col2:
    published_year = st.number_input(
        "Published year",
        value=selected_book.get("published_year"),
        min_value=0,
        max_value=2023,
    )
    book_pageN = st.number_input(
        "Number of pages",
        min_value=0,
        max_value=100_000,
        value=selected_book.get("page_n"),
    )
    book_pageCurrent = st.number_input(
        "Current page",
        min_value=0,
        max_value=100_000,
        value=selected_book.get("page_current"),
    )

with col3:
    book_tag1 = st.text_input("Tag1", value=selected_book.get("tag1"))
    book_tag2 = st.text_input("Tag2", value=selected_book.get("tag2"))
    book_tag3 = st.text_input("Tag3", value=selected_book.get("tag3"))


if st.button("Update book"):
    book = {
        "slug": selected_slug,
        "title": selected_book.get("title"),
        "subtitle": book_subtitle,
        "author": selected_book.get("author"),
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
        "language": selected_book.get("language"),
    }
    success, st.session_state.today_books_df = st.session_state.bk.update_book(
        book, finished, st.session_state.today_books_df
    )
    if success:
        st.success("Books updated!")
    else:
        st.error("Something went wrong, please try again.")

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
