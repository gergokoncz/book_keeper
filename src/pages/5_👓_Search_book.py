#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Search module of the app.

Search your books by name and see event log for them.
"""

from os import environ

import streamlit as st
import streamlit_authenticator as stauth
from streamlit_lottie import st_lottie

from utils import AuthIO, BookKeeperIO, load_lottie_url

# GLOBALS
lottie_asset_url = (
    "https://lottie.host/4b6cf1c6-5ba6-4d4e-896f-64121f952847/sZlE6SNKZf.json"
)


def main() -> None:
    """Main flow of the Search page."""
    st.set_page_config(
        page_title="BookKeeper", page_icon=":closed_book:", layout="wide"
    )

    lottie_add = load_lottie_url(lottie_asset_url)
    st_lottie(lottie_add, speed=1, height=100, key="initial")

    st.markdown(
        """
    ## Search for a book
    Search for a book by title or author (slug),
    and see its history.
    Filter books by properties.
    """
    )

    ## AUTH
    bucket = environ.get("BOOKSTORAGE_BUCKET")
    authio = AuthIO(bucket=bucket)
    config = authio.get_auth_config()

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

        # select book by slug
        not_deleted_books = st.session_state.bk.remove_deleted_books(
            st.session_state.books_df
        )
        not_deleted_books_latest_state = st.session_state.latest_book_state_df.query(
            "deleted==False"
        )
        selected_slug = st.selectbox(  # noqa: F841
            "Select book", not_deleted_books_latest_state["slug"].unique()
        )

        # get the book
        selected_book = not_deleted_books.query("slug==@selected_slug")
        st.write(selected_book.sort_values("current_date", ascending=True))

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
