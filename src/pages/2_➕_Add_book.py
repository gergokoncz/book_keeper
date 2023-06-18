import streamlit as st
import pandas as pd
from os import environ

from utils import BookKeeper, load_lottie_url

st.set_page_config(layout="wide")
bucket = environ.get("BOOKSTORAGE_BUCKET")
bk = BookKeeper("gergokoncz", bucket=bucket)

st.session_state.edited_books_df = pd.DataFrame()

st.markdown(
    """
## Add a new book
Specify the book details below.
"""
)

finished = st.checkbox("Finished - if not ignore Finish date")
finish_date = None

col1, col2, col3 = st.columns(3)

with col1:
    book_title = st.text_input("Title")
    book_subtitle = st.text_input("Subtitle")
    book_author = st.text_input("Author")
    if finished:
        finish_date = st.date_input("Finish date", value=None)

with col2:
    book_location = st.text_input("Location - physical or virtual")
    book_pageN = st.number_input(
        "Number of pages", min_value=0, max_value=100_000, value=100
    )
    book_pageCurrent = st.number_input(
        "Current page", min_value=0, max_value=100_000, value=0
    )

with col3:
    book_tag1 = st.text_input("Tag1")
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
        "pageN": book_pageN,
        "pageCurrent": book_pageCurrent,
        "currentDate": pd.Timestamp.today(),
        "finishDate": finish_date,
        "tag1": book_tag1,
        "tag2": book_tag2,
        "tag3": book_tag3,
        "language": book_language,
    }
    st.session_state.edited_books_df = bk.add_book(book, finished, st.session_state.get("edited_books_df"))
    st.success("Books added!")

if not st.session_state.get("edited_books_df").empty:
    st.write(st.session_state.edited_books_df)
else:
    st.write("No edited books today.")

if st.button("Save updates"):
    saved = bk.save_books(st.session_state.edited_books_df)
    if saved:
        st.session_state.edited_books_df = pd.DataFrame()
        st.success("Books saved!")
