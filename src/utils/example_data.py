#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Utility class with some example data in it."""

import pandas as pd

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
        "publisher": ["Helikon", "Adams Media", "O'Reilly"],
        "published_year": [1934, 2020, 2020],
        "page_n": [512, 252, 399],
        "page_current": [62, 100, 399],
        "started": [True, True, True],
        "deleted": [False, False, False],
        "current_date": [
            pd.Timestamp("2023-06-10"),
            pd.Timestamp("2023-06-10"),
            pd.Timestamp("2023-06-10"),
        ],
        "finish_date": [
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
