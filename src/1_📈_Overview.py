#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is the entry point for BookKeeper app.

Showing some basic statistics of the books that you have logged.
"""

import math
from datetime import datetime, timedelta
from os import environ

import altair as alt
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_lottie import st_lottie

from utils import AuthIO, BookKeeperDataOps, BookKeeperIO, load_lottie_url

# GLOBALS
lottie_asset_url = "https://assets3.lottiefiles.com/packages/lf20_4XmSkB.json"
custom_color_scheme = ["#FF5733", "#33FF57", "#5733FF", "#FFFF33", "#33FFFF"]

two_weeks_ago = datetime.today() - timedelta(days=14)


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

        # GET DATA

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

        # DATA OPERATIONS

        bkdata = BookKeeperDataOps()
        latest_books_with_state_df = bkdata.add_books_state(
            st.session_state.bk.remove_deleted_books(
                st.session_state.latest_book_state_df
            )
        )

        ## BOOKS currently in progress
        in_progress_books = latest_books_with_state_df.query("state == 'in progress'")
        in_progress_books["progress_perc"] = in_progress_books.apply(
            lambda x: round(x["page_current"] / x["page_n"] * 100, 2), axis=1
        )

        in_progress_book_titles = in_progress_books["slug"].tolist()  # noqa: F841

        earliest_log_date_current = bkdata.get_earliest_log_for_books(  # noqa: F841
            slugs=in_progress_book_titles, books_df=st.session_state.books_df
        ) - pd.DateOffset(days=3)

        filled_up_df = bkdata.fill_up_dataframe(st.session_state.books_df)

        summed_pages = (
            filled_up_df.groupby("log_created_at")
            .agg({"page_current": "sum"})
            .reset_index()
        )

        filled_up_currently_reading = filled_up_df.query(
            "slug in @in_progress_book_titles and log_created_at >= @earliest_log_date_current"
        )

        st.write("## Books currently in progress")

        col_counter = 4
        row_counter = math.ceil(in_progress_books.shape[0] / col_counter)
        cols = st.columns(col_counter)

        for row in range(row_counter):
            for col in range(col_counter):
                if row * col_counter + col >= in_progress_books.shape[0]:
                    break
                book = in_progress_books.iloc[row * col_counter + col]
                two_weeks_ago_pagecount_log = (
                    bkdata.get_closest_date_pagecount_for_book(
                        filled_up_currently_reading, book["slug"], date=two_weeks_ago
                    )
                )
                with cols[col]:
                    metric_delta = round(
                        book["progress_perc"]
                        - (
                            two_weeks_ago_pagecount_log["page_current"]
                            / book["page_n"]
                            * 100
                        ),
                        2,
                    )
                    st.metric(
                        label=f"{book['title']}",
                        value=f"{book['progress_perc']} %",
                        delta=f"{metric_delta} %",
                    )

        ## Show reading statistics
        st.divider()

        ## PLOTS

        fig_currently_reading = (
            alt.Chart(
                filled_up_currently_reading,
                title="Pages read over time - books in progress",
            )
            .mark_line(opacity=0.8, size=6)
            .encode(
                x=alt.X("log_created_at", title="date"),
                y=alt.Y("page_current", title="pages read"),
                color=alt.Color(
                    "slug",
                    scale=alt.Scale(scheme="accent"),
                    legend=alt.Legend(orient="top", columns=5, symbolType="stroke"),
                ),
            )
        )

        summed_pages["smoothed_page_current"] = (
            summed_pages["page_current"].ewm(span=20).mean()
        )

        fig_read_pages_all = (
            alt.Chart(summed_pages, title="Pages read over time")
            .mark_line(opacity=0.8, color="#f5bf42", size=4)
            .encode(
                x=alt.X("log_created_at", title="date"),
                y=alt.Y("smoothed_page_current", title="pages read"),
            )
        )

        # three_month_ago = pd.to_datetime("today") - pd.DateOffset(months=3) # noqa: F841
        # last_three_month_df = summed_pages.query("current_date > @three_month_ago")
        # fig_read_pages_last_3_months = (
        #     alt.Chart(last_three_month_df, title="Pages read over time")
        #     .mark_line(opacity=0.8, color="#f5bf42", size=4)
        #     .encode(
        #         x=alt.X("log_created_at", title="date"),
        #         y=alt.Y("page_current", title="pages read"),
        #     )
        # )
        fig_books_ratio = (
            alt.Chart(
                latest_books_with_state_df, title="Books by current state of progress"
            )
            .mark_arc(opacity=0.8)
            .encode(
                color=alt.Color("state", scale=alt.Scale(scheme="accent")),
                theta="count()",
            )
        )

        fig_books_by_published_date = (
            alt.Chart(
                latest_books_with_state_df.query("published_year > 0"),
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
                latest_books_with_state_df.query("published_year > 2000"),
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
            st.altair_chart(fig_read_pages_all, use_container_width=True)
            st.altair_chart(fig_books_by_published_date, use_container_width=True)

        with chart_col2:
            # st.altair_chart(fig_read_pages_last_3_months, use_container_width=True)
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
