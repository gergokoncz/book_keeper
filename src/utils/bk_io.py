#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BookKeeper data IO focused module of the app.

With classes and functions related to CRUD operations on the data.
"""

import re
from os import environ
from typing import Any, Tuple

import pandas as pd
from psycopg2 import ProgrammingError
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Integer,
    MetaData,
    UniqueConstraint,
    String,
    Table,
    create_engine,
    inspect,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.dml import Insert

from .example_data import EXAMPLE_DATA

# init the sql engine
host = environ.get("PG_HOST")
user = environ.get("PG_USER")
password = environ.get("PG_PASSWORD")
schema = environ.get("PG_SCHEMA")

engine = create_engine(f"postgresql://{user}:{password}@{host}:5432/admin_db")


class BookKeeperIO:
    """Class to handle the IO operations of the BookKeeper app."""

    def __init__(self, user_id: str):
        """
        Class constructor.

        :param user_id: the id of the user
        :type user_id: str
        :param bucket: the name of the bucket
        :type bucket: str
        """
        self.user_id = user_id

        self.sql_engine = engine
        self.schema = schema
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.sql_engine, schema=self.schema)

        self.existing_book_slugs: set[str] = set()

    # public methods
    def get_updated_tables(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Update the user's book list, today's batch and the latest state of the books.

        :return: the user's book list, today's batch and the latest state of the books
        :rtype: Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        """
        books_df = self._get_all_books()

        if not books_df.empty:
            today = pd.Timestamp.today().normalize().date()  # noqa: F841
            today_batch_df = books_df.query("log_created_at==@today")
            latest_state_df = self._get_latest_book_version(
                books_df, date_col="log_created_at"
            )

        return books_df, today_batch_df, latest_state_df

    def save_books(self, df: pd.DataFrame) -> bool:
        """
        Save the dataframe to the user's table.

        Works with daily logs.
        Drops all previous logs from that date.
        Writes the table.

        :param df: the dataframe to save
        :type df: pd.DataFrame

        :return: whether the dataframe was saved or not
        :rtype: bool
        """
        if not self._user_table_exists():
            self._create_user_table()

        try:
            with self.sql_engine.connect() as conn:
                for _, row in df.iterrows():
                    stmt = self._get_upsert_daily_book_log_stmt(dict(row))
                    conn.execute(stmt)

                conn.commit()
            return True
        except ProgrammingError:
            return False

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
        book["slug"] = self._create_slug(book)

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
        self, slug: str, today_df: pd.DataFrame
    ) -> Tuple[bool, pd.DataFrame]:
        """
        Revert the deletion of a book.

        Can only be done on the same day deletion took place.

        :param slug: the slug of the book to revert
        :type slug: str
        :param today_df: the dataframe to revert the book in
        :type today_df: pd.DataFrame

        :return: whether the book was reverted or not, the dataframe with the book reverted
        :rtype: Tuple[bool, pd.DataFrame]
        """
        if slug in set(today_df["slug"].unique().tolist()):
            today_df.loc[today_df["slug"] == slug, "deleted"] = False
            return True, today_df

        return False, today_df

    def get_upsert_daily_book_log_stmt(self, book: dict[str, Any]) -> bool:
        """
        Upsert the daily book log.

        :param book: the book to upsert
        :type book: dict[str, Any]

        :return: whether the book was upserted or not
        :rtype: bool
        """
        table_name = f"{self.schema}.{self.user_id}_book_logs"
        table = self.metadata.tables[table_name]

        book = {k: v for k, v in book.items() if k != "id"}  # filter out the id

        stmt = insert(table).values(**book)
        stmt = stmt.on_conflict_do_update(
            index_elements=["slug", "log_created_at"],
            set_={
                "title": stmt.excluded.title,
                "subtitle": stmt.excluded.subtitle,
                "author": stmt.excluded.author,
                "location": stmt.excluded.location,
                "publisher": stmt.excluded.publisher,
                "published_year": stmt.excluded.published_year,
                "page_n": stmt.excluded.page_n,
                "page_current": stmt.excluded.page_current,
                "finish_date": stmt.excluded.finish_date,
                "tag1": stmt.excluded.tag1,
                "tag2": stmt.excluded.tag2,
                "tag3": stmt.excluded.tag3,
                "language": stmt.excluded.language,
                "started": stmt.excluded.page_current > 0,
                "deleted": stmt.excluded.deleted,
            },
        )

        return stmt

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

        book_to_be_deleted = latest_df.loc[latest_df["slug"] == slug].to_dict(
            "records"
        )[0]
        today_df = self._append_book_to_df(
            book=book_to_be_deleted, finished=False, df=today_df, deleted=True
        )
        return True, today_df

    def remove_deleted_books(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove deleted books from the given dataframe.

        :param df: the dataframe to remove deleted books from
        :type df: pd.DataFrame

        :return: the dataframe without the deleted books
        :rtype: pd.DataFrame
        """
        deleted_books = self._get_deleted_books(df)  # noqa: F841
        return df.query("slug not in @deleted_books")

    # private methods
    def _get_all_books(self) -> pd.DataFrame:
        """
        Get all the user's books.

        Including deleted books.
        Everything that is stored in DB.

        :return: the user's books
        :rtype: pd.DataFrame
        """
        if self._user_table_exists():
            books_df = pd.read_sql(
                f"SELECT * FROM {self.schema}.{self.user_id}_book_logs",
                self.sql_engine,
            )
            self.existing_book_slugs = set(books_df["slug"].unique().tolist())
            return books_df

        return EXAMPLE_DATA

    def _user_table_exists(self) -> bool:
        """
        Check if the user's table exists.

        :return: whether the table exists or not
        :rtype: bool
        """
        inspector = inspect(self.sql_engine)
        return inspector.has_table(f"{self.user_id}_book_logs", schema=self.schema)

    def _get_latest_book_version(
        self, books_df: pd.DataFrame, date_col: str
    ) -> pd.DataFrame:
        """
        Get the latest version of the books.

        :param books_df: the dataframe with all the books
        :type books_df: pd.DataFrame

        :return: the latest version of the books
        :rtype: pd.DataFrame
        """
        latest_update_per_book = (
            books_df.groupby("slug").agg({date_col: "max"}).reset_index()
        )
        return pd.merge(
            books_df, latest_update_per_book, on=["slug", date_col], how="inner"
        )

    def _create_user_table(self) -> bool:
        """
        Create the user's table in the database.

        :return: whether the table was created or not
        :rtype: bool
        """
        try:
            _ = Table(
                f"{self.user_id}_book_logs",
                self.metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("title", String),
                Column("subtitle", String),
                Column("author", String),
                Column("location", String),
                Column("publisher", String),
                Column("published_year", Integer),
                Column("page_n", Integer),
                Column("page_current", Integer),
                Column("finish_date", Date),
                Column("tag1", String),
                Column("tag2", String),
                Column("tag3", String),
                Column("language", String),
                Column("slug", String, index=True),
                Column("started", Boolean),
                Column("deleted", Boolean),
                Column("log_created_at", Date, index=True),
                UniqueConstraint("slug", "log_created_at", name="unique_slug_date"),
                schema=self.schema,
            )
            self.metadata.create_all(self.sql_engine)
            self.metadata.reflect(bind=self.sql_engine, schema=self.schema)

            return True
        except ProgrammingError:
            return False

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

        book["log_created_at"] = pd.to_datetime("today").normalize().date()
        book["deleted"] = deleted
        book["started"] = book["page_current"] > 0

        if not finished:
            book["finish_date"] = None

        if df.empty:
            new_df = pd.DataFrame([book])
        else:
            new_df = pd.concat([df, pd.DataFrame([book])], ignore_index=True)
        return new_df

    def _get_upsert_daily_book_log_stmt(self, book: dict[str, Any]) -> Insert:
        """
        Upsert the daily book log.

        :param book: the book to upsert
        :type book: dict[str, Any]

        :return: the SQL statement to upsert the book
        :rtype: sqlalchemy.sql.dml.Insert
        """
        table_name = f"{self.schema}.{self.user_id}_book_logs"
        table = self.metadata.tables[table_name]

        book = {k: v for k, v in book.items() if k != "id"}  # filter out the id

        stmt = insert(table).values(**book)
        stmt = stmt.on_conflict_do_update(
            index_elements=["slug", "log_created_at"],
            set_={
                "title": stmt.excluded.title,
                "subtitle": stmt.excluded.subtitle,
                "author": stmt.excluded.author,
                "location": stmt.excluded.location,
                "publisher": stmt.excluded.publisher,
                "published_year": stmt.excluded.published_year,
                "page_n": stmt.excluded.page_n,
                "page_current": stmt.excluded.page_current,
                "finish_date": stmt.excluded.finish_date,
                "tag1": stmt.excluded.tag1,
                "tag2": stmt.excluded.tag2,
                "tag3": stmt.excluded.tag3,
                "language": stmt.excluded.language,
                "started": stmt.excluded.page_current > 0,
                "deleted": stmt.excluded.deleted,
            },
        )

        return stmt

    def _get_deleted_books(self, df: pd.DataFrame) -> set:
        """
        Get the deleted books.

        :param df: the dataframe to get the deleted books from
        :type df: pd.DataFrame

        :return: the deleted books
        :rtype: set
        """
        return set(df.query("deleted==True")["slug"].unique().tolist())

    @staticmethod
    def _create_slug(book: dict[str, Any]) -> str:
        """
        Create a slug for the book.

        :param book: the book to create the slug for
        :type book: dict[str, Any]

        :return: the slug of the book
        :rtype: str
        """
        author = (
            re.sub(r"[^a-zA-Z0-9\s-]", "", book["author"]).replace(" ", "-").lower()
        )
        title = re.sub(r"[^a-zA-Z0-9\s-]", "", book["title"]).replace(" ", "-").lower()
        return f"{author}-{title}"
