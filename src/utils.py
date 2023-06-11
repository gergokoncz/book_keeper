import pandas as pd
import awswrangler as wr

EXAMPLE_DATA = pd.DataFrame({
    "book_id": [1, 2, 3],
    "title": ["Egy polgar vallomasai", "Personal Finance 101", "Learning Spark"],
    "subtitle": ["", "From saving and investing to taxes and loans, an essential primer on personal finance", "Lightning-Fast Data Analytics"],
    "author": ["Marai Sandor", "Alfred Mill", "Jules S. Damji"],
    "location": ["shelf", "coding/bigdata/scala/LearningSpark", "knowledge101"],
    "pageN": [512, 252, 399],
    "pageCurrent": [62, 100, 399],
    "currentDate": [pd.Timestamp("2023-06-10"), pd.Timestamp("2021-06-10"), pd.Timestamp("2021-06-10")],
    "finishDate": [None, None, pd.Timestamp("2023-03-31")],
    "tags": [{"classic", "hungarian"}, {"finance", "economics"}, {"bigdata", "spark", "scala", "data engineering"}],
    "language": ["hu", "en", "en"],
})


class BookKeeper:
    def __init__(self, user_id: str):
        self.user_id = user_id

    def get_user_books(self) -> pd.DataFrame:
        return EXAMPLE_DATA

    def save_books(self, df: pd.DataFrame) -> bool:
        wr.s3.to_parquet(
            
        )
