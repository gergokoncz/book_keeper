#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The utility class of the app.

With classes and functions for IO and data manipulation.
"""
import time
from enum import Enum
from os import environ
from typing import Any, Optional, Tuple

import awswrangler as wr
import boto3
import pandas as pd
import requests
import yaml
from yaml.loader import SafeLoader

from athena_queries import CREATE_LATEST_UPDATE_PER_BOOK_QUERY
from example_data import EXAMPLE_DATA


class BookState(Enum):
    """Possible values for the state of the books."""

    NOT_STARTED = "not started"
    IN_PROGRESS = "in progress"
    FINISHED = "finished"


# init global variables
athena_client = boto3.client("athena", region_name="eu-north-1")
athena_result_bucket = environ.get("ATHENA_RESULT_BUCKET")

s3_client = boto3.client("s3", region_name="eu-north-1")


class AuthIO:
    """Class to handle the IO operations of the authentication."""

    def __init__(self, bucket: str) -> None:
        """Class constructor."""
        self.bucket = bucket
        self.config_filepath = "config/auth_config.yaml"

    def get_auth_config(self) -> dict[str, Any]:
        """
        Get the contents of the authentication file.

        :return: contents of the to the authentication file
        :rtype: dict[str, Any]
        """
        result = s3_client.get_object(Bucket=self.bucket, Key=self.config_filepath)
        return yaml.load(result["Body"], Loader=SafeLoader)

    def update_auth_config(self, config: dict[str, Any]) -> bool:
        """
        Update the authentication file.

        :param auth_file: the path to the authentication file
        :type auth_file: str
        """
        yaml_content = yaml.dump(config, default_flow_style=False)
        try:
            s3_client.put_object(
                Body=yaml_content, Bucket=self.bucket, Key=self.config_filepath
            )
            return True
        except Exception:  # noqa: B902
            return False


class BookKeeperDataOps:
    """Class to handle the data related operations of the BookKeeper app."""

    def __init__(self) -> None:
        """Class constructor."""
        ...

    def fillup_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fill up the dataframe with missing rows.

        Not all books are kept in all days but for some operations
        we need the dataframe in a format like that.
        For each date

        :param df: the dataframe to fill up
        :type df: pd.DataFrame

        :return: the dataframe filled up
        :rtype: pd.DataFrame
        """
        return df

    def add_books_state(self, latest_books_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add the state of the book to the dataframe.

        :param latest_books_df: the dataframe of the latest books
        :type latest_books_df: pd.DataFrame

        :return: the dataframe updated with the state of the books
        :rtype: pd.DataFrame
        """
        latest_books_df.loc[:, "state"] = BookState.NOT_STARTED.value
        latest_books_df.loc[
            latest_books_df["page_current"] > 0, "state"
        ] = BookState.IN_PROGRESS.value
        latest_books_df.loc[
            ~pd.isnull(latest_books_df["finish_date"]), "state"
        ] = BookState.FINISHED.value

        return latest_books_df


class BookKeeperIO:
    """Class to handle the IO operations of the BookKeeper app."""

    def __init__(self, user_id: str, bucket: str):
        """
        Class constructor.

        :param user_id: the id of the user
        :type user_id: str
        :param bucket: the name of the bucket
        :type bucket: str
        """
        self.user_id = user_id
        self.bucket = bucket
        self.existing_book_slugs: set[str] = set()
        self.books_table_schema = {
            "title": "string",
            "subtitle": "string",
            "author": "string",
            "location": "string",
            "publisher": "string",
            "published_year": "int",
            "page_n": "int",
            "page_current": "int",
            "current_date": "timestamp",
            "finish_date": "timestamp",
            "tag1": "string",
            "tag2": "string",
            "tag3": "string",
            "language": "string",
            "slug": "string",
            "started": "boolean",
            "deleted": "boolean",
        }

    @staticmethod
    def _poll_for_athena_query(query_execution_id: str) -> str:
        """
        Poll for the status of the Athena query.

        Response can be
        QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED

        :param query_execution_id: the id of the query execution
        :type query_execution_id: str

        :return: the status of the query
        :rtype: str
        """
        while True:
            time.sleep(1)
            response = athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            status = response["QueryExecution"]["Status"]["State"]
            if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
                return status

    @staticmethod
    def create_slug(book: dict[str, Any]) -> str:
        """
        Create a slug for the book.

        :param book: the book to create the slug for
        :type book: dict[str, Any]

        :return: the slug of the book
        :rtype: str
        """
        return "-".join(
            [
                book["author"].replace(".", "").replace(" ", "-"),
                book["title"].replace(".", "").replace(" ", "-"),
            ]
        ).lower()

    def _append_book_to_df(
        self,
        book: dict[str, Any],
        finished: bool,
        df: pd.DataFrame,
        deleted: bool = False,
    ) -> pd.DataFrame:
        """
        Append a new book to the dataframe.

        :param book: the book to append
        :type book: dict[str, Any]
        :param finished: whether the book is finished or not
        :type finished: bool
        :param df: the dataframe to append the book to
        :type df: pd.DataFrame
        :param deleted: whether the book is deleted or not, defaults to False
        :type deleted: bool, optional

        :return: the dataframe with the book appended
        :rtype: pd.DataFrame
        """
        if type(book["finish_date"]) != type(pd.to_datetime("today")):  # noqa: E721
            book["finish_date"] = pd.to_datetime(book["finish_date"])

        book["current_date"] = pd.to_datetime("today").normalize()
        book["deleted"] = deleted
        book["started"] = book["page_current"] > 0

        if not finished:
            book["finish_date"] = None

        if df.empty:
            new_df = pd.DataFrame([book])
        else:
            new_df = pd.concat([df, pd.DataFrame([book])], ignore_index=True)
        return new_df

    def add_book(
        self, book: dict[str, Any], finished: bool, df: pd.DataFrame
    ) -> Tuple[bool, pd.DataFrame]:
        """
        Add a new book to the user's book list.

        :param book: the book to add
        :type book: dict[str, Any]
        :param finished: whether the book is finished or not
        :type finished: bool
        :param df: the dataframe to add the book to
        :type df: pd.DataFrame

        :return: whether the book was added or not, the dataframe with the book added
        :rtype: Tuple[bool, pd.DataFrame]
        """
        book["slug"] = self.create_slug(book)

        todays_books_slugs = (
            set(df["slug"].unique().tolist()) if not df.empty else set()
        )
        if book["slug"] in todays_books_slugs.union(self.existing_book_slugs):
            return False, df

        return True, self._append_book_to_df(book=book, finished=finished, df=df)

    def update_book(
        self, book: dict[str, Any], finished: bool, df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Update an existing book.

        :param book: the book to update
        :type book: dict[str, Any]
        :param finished: whether the book is finished or not
        :type finished: bool
        :param df: the dataframe to update the book in
        :type df: pd.DataFrame

        :return: the dataframe with the book updated
        :rtype: pd.DataFrame
        """
        ## some logic needed to handle the update
        todays_books_slugs = (
            set(df["slug"].unique().tolist()) if not df.empty else set()
        )

        if book["slug"] in todays_books_slugs.union(self.existing_book_slugs):
            df = df.drop(df[df["slug"] == book["slug"]].index)

        return True, self._append_book_to_df(book=book, finished=finished, df=df)

    def revert_deletion_book(
        self, slug: str, today_df: pd.DataFrame, latest_df: pd.DataFrame
    ) -> Tuple[bool, pd.DataFrame]:
        """
        Revert the deletion of a book.

        Can only be done on the same day deletion took place.

        :param slug: the slug of the book to revert
        :type slug: str
        :param today_df: the dataframe to revert the book in
        :type today_df: pd.DataFrame
        :param latest_df: the latest dataframe of the user's books
        :type latest_df: pd.DataFrame

        :return: whether the book was reverted or not, the dataframe with the book reverted
        :rtype: Tuple[bool, pd.DataFrame]
        """
        if slug in set(today_df["slug"].unique().tolist()):
            today_df.loc[today_df["slug"] == slug, "deleted"] = False
            return True, today_df
        else:
            return False, today_df

    def delete_book(
        self, slug: str, today_df: pd.DataFrame, latest_df: pd.DataFrame
    ) -> Tuple[bool, pd.DataFrame]:
        """
        Delete a book from the user's book list.

        :param slug: the slug of the book to delete
        :type slug: str
        :param today_df: the dataframe to delete the book from
        :type today_df: pd.DataFrame
        :param latest_df: the latest dataframe of the user's books
        :type latest_df: pd.DataFrame

        :return: whether the book was deleted or not, the dataframe with the book deleted
        :rtype: Tuple[bool, pd.DataFrame]
        """
        if slug in set(today_df["slug"].unique().tolist()):
            today_df.loc[today_df["slug"] == slug, "deleted"] = True
            return True, today_df
        else:
            book_to_be_deleted = latest_df.loc[latest_df["slug"] == slug].to_dict(
                "records"
            )[0]
            today_df = self._append_book_to_df(
                book=book_to_be_deleted, finished=False, df=today_df, deleted=True
            )
            return True, today_df

    def get_deleted_books(self, df: pd.DataFrame) -> set:
        """
        Get the deleted books.

        :param df: the dataframe to get the deleted books from
        :type df: pd.DataFrame

        :return: the deleted books
        :rtype: set
        """
        return set(df.query("deleted==True")["slug"].unique().tolist())

    def get_all_books(self) -> pd.DataFrame:
        """
        Get all the user's books.

        Including deleted books.
        Everything that is stored in S3.

        :return: the user's books
        :rtype: pd.DataFrame
        """
        if self.search_user_table():
            books_df = wr.athena.read_sql_table(
                table=f"{self.user_id}_books",
                database="book_keeper",
                # ctas_approach=False,
                # unload_approach=True
            )
            self.existing_book_slugs = set(books_df["slug"].unique().tolist())
            return books_df
        else:
            return EXAMPLE_DATA

    def remove_deleted_books(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove deleted books from the given dataframe.

        :param df: the dataframe to remove deleted books from
        :type df: pd.DataFrame

        :return: the dataframe without the deleted books
        :rtype: pd.DataFrame
        """
        deleted_books = self.get_deleted_books(df)  # noqa: F841
        return df.query("slug not in @deleted_books")

    def get_books(self) -> pd.DataFrame:
        """
        Get the user's books.

        Filter out deleted books.

        :return: the user's books
        :rtype: pd.DataFrame
        """
        all_books_df = self.get_all_books()
        deleted_books = self.get_deleted_books(all_books_df)  # noqa: F841
        return all_books_df.query("slug not in @deleted_books")

    def save_books(self, df: pd.DataFrame) -> bool:
        """
        Save the dataframe to the user's table.

        :param df: the dataframe to save
        :type df: pd.DataFrame

        :return: whether the dataframe was saved or not
        :rtype: bool
        """
        try:
            wr.s3.to_parquet(
                df=df,
                dtype=self.books_table_schema,
                path=f"s3://{self.bucket}/{self.user_id}/books/",
                dataset=True,
                database="book_keeper",
                table=f"{self.user_id}_books",
                mode="overwrite_partitions",
                partition_cols=["current_date"],
            )
            return True
        except Exception:  # noqa: B902
            return False

    def search_user_table(self) -> bool:
        """
        Search for the user's table in AWS Glue Catalog.

        :return: whether the table exists or not
        :rtype: bool
        """
        return wr.catalog.does_table_exist(
            table=f"{self.user_id}_books", database="book_keeper"
        )

    def get_latest_book_version(self, books_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get the latest version of the books.

        :param books_df: the dataframe with all the books
        :type books_df: pd.DataFrame

        :return: the latest version of the books
        :rtype: pd.DataFrame
        """
        latest_update_per_book = (
            books_df.groupby("slug").agg({"current_date": "max"}).reset_index()
        )
        return pd.merge(
            books_df, latest_update_per_book, on=["slug", "current_date"], how="inner"
        )

    def update_tables(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Update the user's book list, today's batch and the latest state of the books.

        :return: the user's book list, today's batch and the latest state of the books
        :rtype: Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        """
        books_df = self.get_all_books()

        if not books_df.empty:
            today = pd.Timestamp.today().normalize()  # noqa: F841
            today_batch_df = books_df.query("current_date==@today")
            latest_state_df = self.get_latest_book_version(books_df)

        return books_df, today_batch_df, latest_state_df

    def create_latest_book_update_view(self) -> bool:
        """
        Create the latest book update view through athena query.

        :return: whether the view was created or not
        :rtype: bool
        """
        query = CREATE_LATEST_UPDATE_PER_BOOK_QUERY.format(self.user_id, self.user_id)
        self._run_athena_query(query)
        return True

    def _run_athena_query(self, query: str) -> bool:
        return wr.athena.start_query_execution(
            sql=query, database="book_keeper", wait=True
        )


def load_lottie_url(url: str) -> Optional[dict]:
    """
    Load the lottie file located at given url.

    :param url: the url to load
    :type url: str

    :return: the lottie file if request was successful
    :rtype: Optional[dict]
    """
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
