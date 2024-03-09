#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is the entry point for BookKeeper app.

Showing the statistics of the books that you have logged.
"""

import math
from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from utils import BookKeeperDataOps, authenticated_with_data

# VARS
OVERVIEW_LOTTIE_URL = "https://assets3.lottiefiles.com/packages/lf20_4XmSkB.json"
TWO_WEEKS_AGO = datetime.today() - timedelta(days=14)


@authenticated_with_data(
    lottie_url=OVERVIEW_LOTTIE_URL,
    title="BookKeeper",
    description="Keep track of the books you read or you plan to read.",
)
def main() -> None:
    """Main flow of the Overview page."""
    bkdata = BookKeeperDataOps()
    latest_books_with_state_df = bkdata.add_books_state(
        st.session_state.bk.remove_deleted_books(st.session_state.latest_book_state_df)
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
    st.write(summed_pages)

    filled_up_currently_reading = filled_up_df.query(
        "slug in @in_progress_book_titles and log_created_at >= @earliest_log_date_current"
    )

    summed_pages["smoothed_page_current"] = (
        summed_pages["page_current"].ewm(span=15).mean()
    )

    # UI

    st.markdown("### Your main KPIs")

    main_cols = st.columns(3)
    with main_cols[0]:
        st.metric(
            "Books read",
            latest_books_with_state_df.query("state == 'finished'").shape[0],
        )
    with main_cols[1]:
        st.write()

    st.divider()

    ## Currently read books

    with st.expander("Books currently in progress", expanded=True):
        st.write("### Books currently in progress")

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
                        filled_up_currently_reading,
                        book["slug"],
                        date=TWO_WEEKS_AGO,
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

        filled_up_currently_reading["smoothed_page_current"] = (
            filled_up_currently_reading["page_current"].ewm(span=3).mean()
        )

        fig_currently_reading = (
            alt.Chart(
                filled_up_currently_reading,
                title="Pages read over time - books in progress",
            )
            .mark_line(opacity=0.9, size=3)
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

        st.altair_chart(fig_currently_reading, use_container_width=True)

    ## Reading stats
    with st.expander("Reading Statistics", expanded=False):
        st.markdown("### Reading Statistics")
        fig_read_pages_all = (
            alt.Chart(summed_pages, title="Pages read over time")
            .mark_line(opacity=0.8, color="#f5bf42", size=4)
            .encode(
                x=alt.X("log_created_at", title="date"),
                y=alt.Y("smoothed_page_current", title="pages read"),
            )
        )

        fig_books_ratio = (
            alt.Chart(
                latest_books_with_state_df,
                title="Books by current state of progress",
            )
            .mark_arc(opacity=0.8)
            .encode(
                color=alt.Color("state", scale=alt.Scale(scheme="accent")),
                theta="count()",
            )
        )

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.altair_chart(fig_read_pages_all, use_container_width=True)

        with chart_col2:
            # st.altair_chart(fig_read_pages_last_3_months, use_container_width=True)
            st.altair_chart(fig_books_ratio, use_container_width=True)

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

    ## Book statistics
    with st.expander("Book statistics", expanded=False):
        fig_books_by_published_date = (
            alt.Chart(
                latest_books_with_state_df.query("published_year > 0"),
                title="Books by published year",
            )
            .mark_bar(opacity=0.7, color="#f5bf42", size=8)
            .encode(
                x=alt.X(
                    "published_year",
                    title="published year",
                    axis=alt.Axis(format="d"),
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
                    "published_year",
                    title="published year",
                    axis=alt.Axis(format="d"),
                ),
                y=alt.Y("count()", title="number of books"),
                color=alt.Color("state", scale=alt.Scale(scheme="accent")),
            )
        )
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.altair_chart(fig_books_by_published_date, use_container_width=True)

        with chart_col2:
            # st.altair_chart(fig_read_pages_last_3_months, use_container_width=True)
            st.altair_chart(
                fig_books_by_published_date_recent, use_container_width=True
            )


if __name__ == "__main__":
    main()
