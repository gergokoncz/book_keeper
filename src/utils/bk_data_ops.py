#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data operations focused module of the app.

With classes and functions related to operations on the dataframes.
"""

from enum import Enum
from typing import Any, Iterable

import boto3
import pandas as pd

s3_client = boto3.client("s3", region_name="eu-north-1")


class BookState(Enum):
    """Possible values for the state of the books."""

    NOT_STARTED = "not started"
    IN_PROGRESS = "in progress"
    FINISHED = "finished"


class BookKeeperDataOps:
    """Class to handle the data related operations of the BookKeeper app."""

    def __init__(self) -> None:
        """Class constructor."""
        ...

    def filter_book_by_property(
        self, colname: str, value: Any, df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Filter the dataframe by given property.

        :param colname: the name of the column to filter by
        :type colname: str
        :param value: the value to filter by
        :type value: Any
        :param df: the dataframe to filter
        :type df: pd.DataFrame

        :return: the filtered dataframe
        :rtype: pd.DataFrame
        """
        return df.query(f"{colname}==@value")

    def filter_books(
        self,
        latest_book_state_df: pd.DataFrame,
        s_author: str,
        s_published_year_min: int,
        s_published_year_max: int,
        s_publisher: str,
    ) -> pd.DataFrame:
        """
        Filter the books by given properties.

        :param latest_book_state_df: the dataframe to filter
        :type latest_book_state_df: pd.DataFrame
        :param s_author: the author to filter by
        :type s_author: str
        :param s_published_year_min: the min published year to filter by
        :type s_published_year_min: int
        :param s_published_year_max: the max published year to filter by
        :type s_published_year_max: int
        :param s_publisher: the publisher to filter by
        :type s_publisher: str

        :return: the filtered dataframe
        :rtype: pd.DataFrame
        """
        filtered_df = latest_book_state_df
        if s_author:
            filtered_df = filtered_df.query("author==@s_author")
        if s_publisher:
            filtered_df = filtered_df.query("publisher==@s_publisher")
        if s_published_year_min:
            filtered_df = filtered_df.query("published_year>=@s_published_year_min")
        if s_published_year_max:
            filtered_df = filtered_df.query("published_year<=@s_published_year_max")
        return filtered_df

    def get_logs_for_book(self, books_df: pd.DataFrame, slug: str) -> pd.DataFrame:
        """
        Get the logs for a given book.

        :param slug: the slug of the book to get the logs for
        :type slug: str
        :param books_df: the dataframe to get the logs from
        :type books_df: pd.DataFrame

        :return: the logs for the given book
        :rtype: pd.DataFrame
        """
        return books_df.query(f"slug=='{slug}'")

    def get_closest_date_pagecount_for_book(
        self, books_df: pd.DataFrame, slug: str, date: pd.Timestamp
    ) -> pd.DataFrame:
        """
        Get the logs for a given book.

        :param slug: the slug of the book to get the logs for
        :type slug: str
        :param books_df: the dataframe to get the logs from
        :type books_df: pd.DataFrame

        :return: the logs for the given book
        :rtype: pd.DataFrame
        """
        logs_for_book = self.get_logs_for_book(books_df, slug)
        sorted_logs = logs_for_book.sort_values(by="log_created_at", ascending=True)
        return sorted_logs.iloc[sorted_logs["log_created_at"].searchsorted(date)]

    def fill_up_book_df(
        self, book_df: pd.DataFrame, df_dates: Iterable[pd.Timestamp]
    ) -> pd.DataFrame:
        """
        Given current logs for book fill up the dataframe for given dates.

        :param book_df: the dataframe to fill up
        :type book_df: pd.DataFrame
        :param df_dates: the dates to fill up the dataframe for
        :type df_dates: Iterable[pd.Timestamp]

        :return: the dataframe filled up
        :rtype: pd.DataFrame
        """
        latest_log: pd.DataFrame
        rows_to_add: list[pd.DataFrame] = []
        first_log_date = book_df["log_created_at"].min()

        for date in (d for d in df_dates if d >= first_log_date):
            row_for_date = book_df.query(f"log_created_at == '{date}'")

            if row_for_date.shape[0] > 0:
                latest_log = row_for_date.iloc[0]

            else:
                new_row = latest_log.copy()
                new_row["log_created_at"] = date
                rows_to_add.append(new_row)

        return pd.concat([pd.DataFrame(rows_to_add), book_df], axis=0)

    def backdate_books(self, books_df: pd.DataFrame) -> pd.DataFrame:
        """
        Backdate the books.

        When book logs are older than the time they were finished.
        This can happen when the user forgets to log the book for a while.

        :param books_df: the dataframe to backdate
        :type books_df: pd.DataFrame

        :return: the dataframe backdated
        :rtype: pd.DataFrame
        """
        books_df = self.add_books_state(books_df)
        finished_books_df = books_df.query("state=='finished'").copy()
        finished_books_df = finished_books_df.query(
            "log_created_at > finish_date"
        ).copy()
        finished_books_df["log_created_at"] = finished_books_df["finish_date"]
        return finished_books_df

    def fill_up_dataframe(self, books_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fill up the dataframe with missing rows.

        Not all books are kept in all days but for some operations
        we need the dataframe in a format like that.
        For each date

        :param books_df: the dataframe to fill up
        :type df: pd.DataFrame

        :return: the dataframe filled up
        :rtype: pd.DataFrame
        """
        backdated_books_df = self.backdate_books(books_df.copy())
        books_df = pd.concat([books_df, backdated_books_df], axis=0)
        books_df["log_created_at"] = pd.to_datetime(books_df["log_created_at"])
        # sort df by slug and date
        books_df.sort_values(by=["slug", "log_created_at"], inplace=True)

        # create new df with all unique dates
        unique_dates = pd.date_range(
            books_df["log_created_at"].min(), books_df["log_created_at"].max(), freq="D"
        )

        # cross join unique dates with unique slugs
        unique_slugs = books_df["slug"].unique()
        cartesian_product = pd.MultiIndex.from_product(
            [unique_slugs, unique_dates], names=["slug", "log_created_at"]
        )
        cross_join_df = pd.DataFrame(index=cartesian_product).reset_index()

        # merge cross join with books_df
        result_df = cross_join_df.merge(
            books_df, how="left", on=["slug", "log_created_at"]
        )

        # sort and reset the index of the result df
        result_df.sort_values(by=["slug", "log_created_at"], inplace=True)
        result_df.reset_index(drop=True, inplace=True)

        # interpolate the missing values
        result_df = result_df.groupby("slug", group_keys=False).apply(
            self._custom_interpolate
        )

        # fill remaining missing values with 0
        result_df.fillna({"page_current": 0}, inplace=True)

        return result_df

    def _custom_interpolate(self, group: pd.DataFrame) -> pd.DataFrame:
        group["page_current"] = group["page_current"].ffill()
        return group

    def get_earliest_log_per_book(books_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get the earliest log per book.

        :param books_df: the with all the book logs
        :type books_df: pd.DataFrame

        :return: the earliest log per book
        :rtype: pd.DataFrame
        """
        return books_df.groupby("slug").agg({"log_created_at": "min"}).reset_index()

    def get_earliest_log_for_books(
        self, slugs: list[str], books_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Get the earliest log for given books.

        Earliest that is present for any of the books.
        :param slugs: the slugs of the books to get the earliest log for
        :type slugs: list[str]
        :param books_df: the dataframe to get the earliest log from
        :type books_df: pd.DataFrame
        """
        filtered_df = books_df.query("slug in @slugs")
        return filtered_df["log_created_at"].min()

    def add_books_state(self, latest_books_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add the state of the book to the dataframe.

        :param latest_books_df: the dataframe of the latest books
        :type latest_books_df: pd.DataFrame

        :return: the dataframe updated with the state of the books
        :rtype: pd.DataFrame
        """
        df_copy = latest_books_df.copy()

        df_copy.loc[:, "state"] = BookState.NOT_STARTED.value
        df_copy.loc[df_copy["page_current"] > 0, "state"] = BookState.IN_PROGRESS.value
        df_copy.loc[~pd.isnull(df_copy["finish_date"]), "state"] = (
            BookState.FINISHED.value
        )

        return df_copy

    def show_books_overview(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Show an overview of the books.

        Return only subset of columns.

        :param df: the dataframe to show the overview for
        :type df: pd.DataFrame

        :return: the dataframe with the overview
        :rtype: pd.DataFrame
        """
        return df[["author", "title", "publisher", "published_year", "page_n"]].rename(
            columns={
                "author": "Author",
                "title": "Book Title",
                "publisher": "Publishing Company",
                "published_year": "Published Year",
                "page_n": "Number of Pages",
            }
        )
