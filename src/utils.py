import pandas as pd
import awswrangler as wr
import requests
import boto3
from typing import Dict, Any, Tuple
import time
from athena_queries import CREATE_LATEST_UPDATE_PER_BOOK_QUERY
from example_data import EXAMPLE_DATA

from os import environ

# init global variables
athena_client = boto3.client("athena", region_name="eu-north-1")
athena_result_bucket = environ.get("ATHENA_RESULT_BUCKET")


class BookKeeperIO:
    """
    Class to handle the IO operations of the BookKeeper app.
    """

    def __init__(self, user_id: str, bucket: str):
        self.user_id = user_id
        self.bucket = bucket
        self.existing_book_slugs = set()
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
        Response can be
        QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED
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
    def create_slug(book: Dict[str, Any]) -> str:
        return "-".join(
            [
                book["author"].replace(".", "").replace(" ", "-"),
                book["title"].replace(".", "").replace(" ", "-"),
            ]
        ).lower()

    def _append_book_to_df(
        self,
        book: dict,
        finished: bool,
        df: pd.DataFrame,
        deleted: bool = False,
    ) -> pd.DataFrame:
        """
        Append a new book to the dataframe.
        """
        if type(book["finish_date"]) != type(pd.to_datetime("today")):
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
        self, book: dict, finished: bool, df: pd.DataFrame
    ) -> Tuple[bool, pd.DataFrame]:
        """
        Add a new book to the user's book list.
        """
        book["slug"] = self.create_slug(book)

        todays_books_slugs = (
            set(df["slug"].unique().tolist()) if not df.empty else set()
        )
        if book["slug"] in todays_books_slugs.union(self.existing_book_slugs):
            return False, df

        return True, self._append_book_to_df(book=book, finished=finished, df=df)

    def update_book(self, book: dict, finished: bool, df: pd.DataFrame) -> pd.DataFrame:
        """
        Update an existing book.
        """
        ## some logic needed to handle the update
        todays_books_slugs = (
            set(df["slug"].unique().tolist()) if not df.empty else set()
        )

        if book["slug"] in todays_books_slugs.union(self.existing_book_slugs):
            df = df.drop(df[df["slug"] == book["slug"]].index)

        return True, self._append_book_to_df(book=book, finished=finished, df=df)

    def delete_book(
        self, slug: str, today_df: pd.DataFrame, latest_df: pd.DataFrame
    ) -> Tuple[bool, pd.DataFrame]:
        """
        Delete a book from the user's book list.
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
        """
        return set(df.query("deleted==True")["slug"].unique().tolist())

    def get_all_books(self) -> pd.DataFrame:
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

    def get_books(self) -> pd.DataFrame:
        """
        Get the user's books.
        """
        all_books_df = self.get_all_books()
        deleted_books = self.get_deleted_books(all_books_df)
        return all_books_df.query("slug not in @deleted_books")

    def save_books(self, df: pd.DataFrame) -> bool:
        """
        Save the dataframe to the user's table.
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
        except Exception as e:
            return False

    def search_user_table(self) -> bool:
        return wr.catalog.does_table_exist(
            table=f"{self.user_id}_books", database="book_keeper"
        )

    def get_latest_book_version(self, books_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get the latest version of the books.
        """
        latest_update_per_book = (
            books_df.groupby("slug").agg({"current_date": "max"}).reset_index()
        )
        return pd.merge(
            books_df, latest_update_per_book, on=["slug", "current_date"], how="inner"
        )

    def update_tables(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Update the user's book list, today's batch and the latest state of the books.
        """
        books_df = self.get_books()

        if not books_df.empty:
            today = pd.Timestamp.today().normalize()
            today_batch_df = books_df.query("current_date==@today")
            latest_state_df = self.get_latest_book_version(books_df)

        return books_df, today_batch_df, latest_state_df

    def create_latest_book_update_view(self) -> bool:
        query = CREATE_LATEST_UPDATE_PER_BOOK_QUERY.format(self.user_id, self.user_id)
        response = self.run_athena_query(query)
        return True

    def _run_athena_query(self, query: str) -> bool:
        return wr.athena.start_query_execution(
            sql=query, database="book_keeper", wait=True
        )


def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
