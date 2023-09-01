#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is the entry point for BookKeeper app.

Showing some basic statistics of the books that you have logged.
"""

from os import environ

import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from streamlit_lottie import st_lottie

from utils import BookKeeperDataOps, BookKeeperIO, load_lottie_url

st.set_page_config(layout="wide")


lottie_books = load_lottie_url(
    "https://assets3.lottiefiles.com/packages/lf20_4XmSkB.json"
)
st_lottie(lottie_books, speed=1, height=100, key="initial")

st.title("BookKeeper")

st.markdown("Keep track of the books you read or you plan to read.")

st.markdown("## Your stats")

with st.spinner("Your books are loading..."):

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

# st.write(
#     st.session_state.bk.remove_deleted_books(st.session_state.latest_book_state_df)
# )

bkdata = BookKeeperDataOps()
latest_books_df = bkdata.add_books_state(
    st.session_state.bk.remove_deleted_books(st.session_state.latest_book_state_df)
)
st.write(latest_books_df)

in_progress_books = latest_books_df.query("state == 'in progress'")
in_progress_books["progress_perc"] = round(
    in_progress_books["page_current"] / in_progress_books["page_n"] * 100, 2
)
# in_progress_books.eval("progress_perc = page_current / page_n")

# fig = plt.figure(figsize=(8, 6))
# plt.title("Books currently in progress")
# sns.barplot(data=in_progress_books, x="title", y="progress_perc")

fig_in_progress = (
    alt.Chart(in_progress_books)
    .mark_bar(opacity=0.6, color="#f5bf42", size=10)
    .encode(
        x=alt.X("title", title="book title"),
        y=alt.Y("progress_perc", title="percentage", scale=alt.Scale(domain=[0, 100])),
    )
    .properties(title="Books currently in progress")
)

st.altair_chart(fig_in_progress, use_container_width=True)


fig = alt.Chart(latest_books_df).mark_bar().encode(x="state", y="count()")
st.altair_chart(fig, use_container_width=True)
