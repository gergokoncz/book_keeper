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

from utils import AuthIO, BookKeeperDataOps, BookKeeperIO, load_lottie_url

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
    Filter books by properties, or search for a book by title and get the detailed logs.
    and see its history.
    """
    )

    st.divider()

    ## AUTH
    bucket = environ.get("BOOKSTORAGE_BUCKET")
    authio = AuthIO(bucket=bucket)
    config = authio.get_auth_config()
    bk_data_ops = BookKeeperDataOps()

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

        # not_deleted_books = st.session_state.bk.remove_deleted_books(
        #     st.session_state.books_df
        # )
        not_deleted_books_latest_state = st.session_state.latest_book_state_df.query(
            "deleted==False"
        )

        # define filters

        # filter by author

        st.markdown("### Configure the filters to find subset of books")

        col1, col2, col3 = st.columns(3)

        with col1:
            selected_author = st.multiselect(
                "Select author", not_deleted_books_latest_state["author"].unique()
            )

            selected_publisher = st.multiselect(
                "Select publisher",
                not_deleted_books_latest_state["publisher"].unique(),
            )

        with col2:
            min_published_year: int = not_deleted_books_latest_state[
                "published_year"
            ].min()
            max_published_year: int = not_deleted_books_latest_state[
                "published_year"
            ].max()

            selected_min_published_year = st.number_input(
                "Minimum published year",
                min_published_year,
                max_published_year,
                min_published_year,
            )

            selected_max_published_year = st.number_input(
                "Maximum published year",
                min_published_year,
                max_published_year,
                max_published_year,
            )

        filtered_books = bk_data_ops.filter_books(
            st.session_state.latest_book_state_df,
            selected_author,
            selected_min_published_year,
            selected_max_published_year,
            selected_publisher,
        )
        st.markdown("Books matching filters")
        st.write(bk_data_ops.show_books_overview(filtered_books))

        # filter by published year

        # filter by tag

        st.divider()
        st.markdown("### Select slug for book and find detailed logs")

        selected_slug = st.selectbox(  # noqa: F841
            "Select book", not_deleted_books_latest_state["slug"].unique()
        )

        # get the book
        selected_book_df = bk_data_ops.get_logs_for_book(
            st.session_state.books_df, selected_slug
        )
        st.write(selected_book_df.sort_values("log_created_at", ascending=True))

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
