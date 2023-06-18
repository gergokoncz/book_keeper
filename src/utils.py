import pandas as pd
import awswrangler as wr
import requests
from datetime import datetime
import boto3
from typing import Dict, Any
import time
from athena_queries import READ_USER_TABLE_QUERY, CREATE_LATEST_UPDATE_BER_BOOK_QUERY

from os import environ

# some dummy data
EXAMPLE_DATA = pd.DataFrame(
    {
        "title": ["Egy polgar vallomasai", "Personal Finance 101", "Learning Spark"],
        "subtitle": [
            "",
            "From saving and investing to taxes and loans, an essential primer on personal finance",
            "Lightning-Fast Data Analytics",
        ],
        "author": ["Marai Sandor", "Alfred Mill", "Jules S. Damji"],
        "location": ["shelf", "coding/bigdata/scala/LearningSpark", "knowledge101"],
        "pageN": [512, 252, 399],
        "pageCurrent": [62, 100, 399],
        "started": [True, True, True],
        "deleted": [False, False, False],
        "currentDate": [
            pd.Timestamp("2023-06-10"),
            pd.Timestamp("2023-06-10"),
            pd.Timestamp("2023-06-10"),
        ],
        "finishDate": [
            pd.Timestamp("1990-01-01"),
            pd.Timestamp("1990-01-01"),
            pd.Timestamp("2023-03-31"),
        ],
        "tag1": ["classic", "finance", "bigdata"],
        "tag2": ["hungarian", "investing", "spark"],
        "tag3": ["", "taxes", "data engineering"],
        "language": ["hu", "en", "en"],
        "slug": [
            "marai-sandor-egy-polgar-vallomasai",
            "alfred-mill-personal-finance-101",
            "jules-s-damji-learning-spark",
        ],
    }
)



athena_client = boto3.client("athena")
athena_result_bucket = environ.get("ATHENA_RESULT_BUCKET")

class BookKeeper:
    def __init__(self, user_id: str, bucket: str):
        self.user_id = user_id
        self.bucket = bucket
        self.data_schema = {
            "title": "string",
            "subtitle": "string",
            "author": "string",
            "location": "string",
            "pageN": "int",
            "pageCurrent": "int",
            "currentDate": "timestamp",
            "finishDate": "timestamp",
            "tag1": "string",
            "tag2": "string",
            "tag3": "string",
            "language": "string",
            "slug": "string",
            "started": "boolean",
            "deleted": "boolean",
        }

    @staticmethod
    def poll_for_athena_query(query_execution_id: str) -> str:
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
            print(status)
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
    
    def create_latest_book_update_view(self) -> bool:
        query = CREATE_LATEST_UPDATE_BER_BOOK_QUERY.format(self.user_id, self.user_id)
        response = self.run_athena_query(query)
        print(response)
        return True

    def add_book(self, book: dict, finished: bool, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add a new book to the user's book list.
        """
        if not finished:
            book["finishDate"] = None
        
        book["currentDate"] = pd.to_datetime("today").normalize()
        book["slug"] = self.create_slug(book)
        book["deleted"] = False
        book["started"] = book["pageCurrent"] > 0
        book["finishDate"] = pd.to_datetime(book["finishDate"])

        if df.empty:
            new_df = pd.DataFrame([book])
        else:
            new_df = pd.concat([df, pd.DataFrame([book])], ignore_index=True)
        
        saved = self.save_books(new_df)
        return new_df

    def get_user_books(self) -> pd.DataFrame:
        read_user_table_query = READ_USER_TABLE_QUERY.format(self.user_id)
        if self.search_user_table():
            print("table exists")
            return wr.athena.read_sql_table(
                table=f"{self.user_id}_books", 
                database="book_keeper",
                # ctas_approach=False,
                # unload_approach=True
            )
        else:
            print("table does not exist")
            return EXAMPLE_DATA
    
    def run_athena_query(self, query: str) -> bool:
        return wr.athena.start_query_execution(sql=query, database="book_keeper", wait=True)

    def search_user_table(self) -> bool:
        return wr.catalog.does_table_exist(
            table=f"{self.user_id}_books", database="book_keeper"
        )

    def save_books(self, df: pd.DataFrame) -> bool:
        try:
            wr.s3.to_parquet(
                df=df,
                dtype=self.data_schema,
                path=f"s3://{self.bucket}/{self.user_id}/books/",
                dataset=True,
                database="book_keeper",
                table=f"{self.user_id}_books",
                mode="overwrite_partitions",
                partition_cols=["currentDate"],
            )
            return True
        except Exception as e:
            print(e)
            return False


def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
