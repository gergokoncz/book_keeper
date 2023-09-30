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
import streamlit_authenticator as stauth
from streamlit_lottie import st_lottie

from utils import AuthIO, BookKeeperDataOps, BookKeeperIO, load_lottie_url

# GLOBALS
lottie_asset_url = "https://assets3.lottiefiles.com/packages/lf20_4XmSkB.json"


def main() -> None:
    """Main flow of the Overview page."""
    st.set_page_config(
        page_title="BookKeeper", page_icon=":closed_book:", layout="wide"
    )

    lottie_books = load_lottie_url(lottie_asset_url)
    st_lottie(lottie_books, speed=1, height=100, key="initial")

    st.title("BookKeeper")

    st.markdown("Keep track of the books you read or you plan to read.")

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

        ## Content of application goes here
        st.write(f"Welcome {st.session_state['name']}!")

        st.markdown("## Your stats")

        with st.spinner("Your books are loading..."):

            if "bk" not in st.session_state:
                st.session_state.bk = BookKeeperIO(
                    st.session_state["username"], bucket=bucket
                )

            # get an update on the tables
            if "books_df" not in st.session_state:
                (
                    st.session_state.books_df,
                    st.session_state.today_books_df,
                    st.session_state.latest_book_state_df,
                ) = st.session_state.bk.update_tables()

        bkdata = BookKeeperDataOps()
        latest_books_df = bkdata.add_books_state(
            st.session_state.bk.remove_deleted_books(
                st.session_state.latest_book_state_df
            )
        )
        st.write(latest_books_df)

        st.write("## Filled up df")
        st.write(bkdata.fillup_dataframe(st.session_state.books_df))

        in_progress_books = latest_books_df.query("state == 'in progress'")
        in_progress_books["progress_perc"] = in_progress_books.apply(
            lambda x: round(x["page_current"] / x["page_n"] * 100, 2), axis=1
        )

        fig_in_progress = (
            alt.Chart(in_progress_books)
            .mark_bar(opacity=0.6, color="#f5bf42", size=10)
            .encode(
                x=alt.X("title", title="book title"),
                y=alt.Y(
                    "progress_perc",
                    title="percentage",
                    scale=alt.Scale(domain=[0, 100]),
                ),
            )
            .properties(title="Books currently in progress")
        )

        st.altair_chart(fig_in_progress, use_container_width=True)

        fig = alt.Chart(latest_books_df).mark_bar().encode(x="state", y="count()")
        st.altair_chart(fig, use_container_width=True)

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
