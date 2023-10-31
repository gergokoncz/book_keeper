#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is the entry point for BookKeeper app.

Showing some basic statistics of the books that you have logged.
"""

from os import environ

import altair as alt
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_lottie import st_lottie

from utils import AuthIO, BookKeeperDataOps, BookKeeperIO, load_lottie_url

# GLOBALS
lottie_asset_url = "https://assets3.lottiefiles.com/packages/lf20_4XmSkB.json"
custom_color_scheme = ["#FF5733", "#33FF57", "#5733FF", "#FFFF33", "#33FFFF"]


def main() -> None:
    """Main flow of the Overview page."""
    ## CONFIG
    st.set_page_config(
        page_title="BookKeeper", page_icon=":closed_book:", layout="wide"
    )

    lottie_books = load_lottie_url(lottie_asset_url)
    st_lottie(lottie_books, speed=1, height=100, key="initial")

    st.title("BookKeeper")

    st.markdown("Keep track of the books you read or you plan to read.")

    st.divider()

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
        # st.write(latest_books_df)

        st.write("## Books currently in progress")

        ## BOOKS currently in progress
        in_progress_books = latest_books_df.query("state == 'in progress'")
        in_progress_books["progress_perc"] = in_progress_books.apply(
            lambda x: round(x["page_current"] / x["page_n"] * 100, 2), axis=1
        )
        st.write(in_progress_books)

        in_progress_book_titles = in_progress_books["slug"].tolist()  # noqa: F841

        cols = st.columns(in_progress_books.shape[0])
        col_counter = 0
        for _, book in in_progress_books.iterrows():
            with cols[col_counter]:
                # st.write(f"{book['title']} - {book['progress_perc']}%")
                st.metric(label=f"{book['title']} (%)", value=book["progress_perc"])
            col_counter += 1

        # fig_in_progress = (
        #     alt.Chart(in_progress_books)
        #     .mark_bar(opacity=0.6, color="#f5bf42", size=20)
        #     .encode(
        #         x=alt.X("title", title="book title"),
        #         y=alt.Y(
        #             "progress_perc",
        #             title="percentage",
        #             scale=alt.Scale(domain=[0, 100]),
        #         ),
        #     )
        #     .properties(title="Books currently in progress")
        # )

        # st.altair_chart(fig_in_progress, use_container_width=True)

        ## Show reading statistics
        st.divider()

        filled_up_df = bkdata.fill_up_dataframe(st.session_state.books_df)

        summed_pages = (
            filled_up_df.groupby("current_date")
            .agg({"page_current": "sum"})
            .reset_index()
        )

        filled_up_currently_reading = filled_up_df.query(
            "slug in @in_progress_book_titles"
        )

        ## PLOTS

        fig_currently_reading = (
            alt.Chart(
                filled_up_currently_reading,
                title="Pages read over time - books in progress",
            )
            .mark_line(opacity=0.8, size=6)
            .encode(
                x=alt.X("current_date", title="date"),
                y=alt.Y("page_current", title="pages read"),
                color=alt.Color(
                    "slug",
                    scale=alt.Scale(scheme="accent"),
                    legend=alt.Legend(
                        orient="top-left", columns=2, symbolType="stroke"
                    ),
                ),
            )
        )

        fig_read_pages = (
            alt.Chart(summed_pages, title="Pages read over time")
            .mark_line(opacity=0.8, color="#f5bf42", size=6)
            .encode(
                x=alt.X("current_date", title="date"),
                y=alt.Y("page_current", title="pages read"),
            )
        )

        fig_books_ratio = (
            alt.Chart(latest_books_df, title="Books by current state of progress")
            .mark_arc(opacity=0.8)
            .encode(
                color=alt.Color("state", scale=alt.Scale(scheme="accent")),
                theta="count()",
            )
        )

        fig_books_by_published_date = (
            alt.Chart(
                latest_books_df.query("published_year > 0"),
                title="Books by published year",
            )
            .mark_bar(opacity=0.7, color="#f5bf42", size=8)
            .encode(
                x=alt.X(
                    "published_year", title="published year", axis=alt.Axis(format="d")
                ),
                y=alt.Y("count()", title="number of books"),
            )
        )
        fig_books_by_published_date_recent = (
            alt.Chart(
                latest_books_df.query("published_year > 2000"),
                title="Books by published year and current state of progress (recent)",
            )
            .mark_bar(opacity=0.8, color="#f5bf42", size=6)
            .encode(
                x=alt.X(
                    "published_year", title="published year", axis=alt.Axis(format="d")
                ),
                y=alt.Y("count()", title="number of books"),
                color=alt.Color("state", scale=alt.Scale(scheme="accent")),
            )
        )
        st.altair_chart(fig_currently_reading, use_container_width=True)
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.altair_chart(fig_read_pages, use_container_width=True)
            st.altair_chart(fig_books_by_published_date, use_container_width=True)

        with chart_col2:
            st.altair_chart(fig_books_ratio, use_container_width=True)
            st.altair_chart(
                fig_books_by_published_date_recent, use_container_width=True
            )

        st.divider()

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
