#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Delete module of the app.

Delete a book from the collection of books that you maintain.
Also revert the deletion on the day you have done it.
"""

from os import environ

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_lottie import st_lottie

from utils import AuthIO, BookKeeperIO, load_lottie_url

# GLOBALS
lottie_asset_url = "https://assets7.lottiefiles.com/packages/lf20_nux6g0kx.json"


def main() -> None:
    """Main flow of the Delete page."""
    st.set_page_config(
        page_title="BookKeeper", page_icon=":closed_book:", layout="wide"
    )

    lottie_add = load_lottie_url(lottie_asset_url)
    st_lottie(lottie_add, speed=1, height=100, key="initial")

    st.markdown(
        """
    ## Delete existing book
    Select the book by slug and confirm delete.
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

        selected_slug_for_deletion = st.selectbox(
            "Select book",
            st.session_state.bk.remove_deleted_books(
                st.session_state.latest_book_state_df
            )["slug"].unique(),
        )

        if st.button("Delete book"):
            success, st.session_state.today_books_df = st.session_state.bk.delete_book(
                selected_slug_for_deletion,
                st.session_state.today_books_df,
                st.session_state.latest_book_state_df,
            )
            if success:
                saved = st.session_state.bk.save_books(st.session_state.today_books_df)
                if saved:
                    st.success("Book deleted!")
                    (
                        st.session_state.books_df,
                        st.session_state.today_books_df,
                        st.session_state.latest_book_state_df,
                    ) = st.session_state.bk.update_tables()
                else:
                    st.error("Something went wrong, please try again.")
            else:
                st.error("Something went wrong, please try again.")

        st.markdown(
            """
        ## Revert deletion of book
        Select slug from deleted books and revert deletion - can only be done on the same day deletion took place.
        """
        )

        today_books_df = st.session_state.today_books_df
        deleted_books_df = today_books_df.query("deleted==True")

        selected_slug_for_revert = st.selectbox(
            "Select book", deleted_books_df["slug"].unique()
        )

        if st.button("Revert deletion"):
            (
                success,
                st.session_state.today_books_df,
            ) = st.session_state.bk.revert_deletion_book(
                selected_slug_for_revert,
                st.session_state.today_books_df,
                st.session_state.latest_book_state_df,
            )
            if success:
                saved = st.session_state.bk.save_books(st.session_state.today_books_df)
                if saved:
                    st.success("Book deletion reverted!")
                    (
                        st.session_state.books_df,
                        st.session_state.today_books_df,
                        st.session_state.latest_book_state_df,
                    ) = st.session_state.bk.update_tables()
                else:
                    st.error("Something went wrong, please try again.")
            else:
                st.error("Something went wrong, please try again.")

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
