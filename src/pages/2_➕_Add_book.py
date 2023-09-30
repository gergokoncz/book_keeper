#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add module of the app.

Add a new book to the collection of books that you maintain.
"""

from os import environ

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_lottie import st_lottie

from utils import AuthIO, BookKeeperIO, load_lottie_url

# GLOBALS
lottie_asset_url = "https://assets6.lottiefiles.com/packages/lf20_hMl7FE.json"


def main() -> None:
    """Main flow of the Add page."""
    st.set_page_config(
        page_title="BookKeeper", page_icon=":closed_book:", layout="wide"
    )

    lottie_add = load_lottie_url(lottie_asset_url)

    st_lottie(lottie_add, speed=1, height=100, key="initial")

    st.markdown(
        """
    ## Add a new book
    Specify the book details below. Most details can be left empty and edited later on the update page.
    The exceptions are the title and the author.
    """
    )

    ## AUTH
    bucket = environ.get("BOOKSTORAGE_BUCKET")
    authio = AuthIO(bucket=bucket)
    config = authio.get_auth_config()
    # success = authio.update_auth_config(config)

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        config["preauthorized"],
    )

    authenticator.login("Login", "main")

    # Present content based on authentication status
    ## If user is authenticated, show the app
    if st.session_state["authentication_status"]:

        authenticator.logout("Logout", "sidebar")

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
            published_year = st.number_input(
                "Published year", min_value=0, max_value=2023
            )
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

        # show edited and deleted books
        today_books_df = st.session_state.today_books_df
        edited_books_df = today_books_df.query("deleted==False")
        deleted_books_df = today_books_df.query("deleted==True")

        if not edited_books_df.empty:
            st.markdown("### Edited books - today")
            st.write(edited_books_df)

        if not deleted_books_df.empty:
            st.markdown("### Deleted books (today)")
            st.write(deleted_books_df)

        if not today_books_df.empty:
            if st.button("Save updates"):
                saved = st.session_state.bk.save_books(st.session_state.today_books_df)
                if saved:
                    st.success("Books saved!")
                    with st.spinner("Updating books..."):
                        (
                            st.session_state.books_df,
                            st.session_state.today_books_df,
                            st.session_state.latest_book_state_df,
                        ) = st.session_state.bk.update_tables()

    ## If user gave wrong credentials
    elif st.session_state["authentication_status"] is False:
        st.error("Username/password is incorrect")

    ## If user has not logged in yet
    elif st.session_state["authentication_status"] is None:
        st.warning("Please enter your username and password")

        # enable registration
        if st.checkbox("New user?"):
            try:
                if authenticator.register_user(
                    "Register user", "main", preauthorization=False
                ):
                    authio.update_auth_config(config)
                    st.success("You have successfully registered!")
            except Exception as e:  # noqa: B902
                st.error(e)


if __name__ == "__main__":
    main()
