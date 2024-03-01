"""Quick script to migrate data from s3 to postgres."""

from os import environ

import awswrangler as wr
import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
)

userid = "xxx"


def get_s3_table() -> pd.DataFrame:
    """Read the s3 table and return it as a dataframe."""
    books_df = wr.athena.read_sql_table(
        table=f"{userid}_books",
        database="book_keeper",
    )

    return books_df


def create_book_logs_table(engine, userid=userid, schema="bookkeeper_prod"):
    """Create the book logs table."""
    conn = engine.connect()

    metadata = MetaData()

    _ = Table(
        f"{userid}_book_logs",
        metadata,
        Column("id", Integer, primary_key=True),
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
        schema=schema,
    )

    metadata.create_all(engine)

    conn.close()


if __name__ == "__main__":
    books_df = get_s3_table()

    # gather db conn
    host = environ.get("PG_HOST")
    user = environ.get("PG_USER")
    password = environ.get("PG_PASSWORD")
    engine = create_engine(f"postgresql://{user}:{password}@{host}:5432/admin_db")

    # create table
    create_book_logs_table(engine, userid=userid, schema="bookkeeper_prod")
    books_df.rename(columns={"current_date": "log_created_at"}, inplace=True)
    books_df[
        [
            "title",
            "subtitle",
            "author",
            "location",
            "publisher",
            "published_year",
            "page_n",
            "page_current",
            "finish_date",
            "tag1",
            "tag2",
            "tag3",
            "language",
            "slug",
            "started",
            "deleted",
            "log_created_at",
        ]
    ].to_sql(
        "example661456_logs",
        engine,
        schema="bookkeeper_prod",
        if_exists="append",
        index=False,
    )
