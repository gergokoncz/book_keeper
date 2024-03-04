#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test module BookKeeperIO."""

import boto3
import pytest

from src.tests.conftest import TEST_BUCKET_NAME, TEST_REGION, TEST_USERNAME
from src.utils import BookKeeperIO


@pytest.fixture(autouse=True)
def before_and_after_test():
    """Fixture to run before and after each test."""
    # Run before test
    yield
    # Run after test
    s3 = boto3.resource("s3", region_name=TEST_REGION)
    bucket = s3.Bucket(TEST_BUCKET_NAME)
    bucket.objects.all().delete()


@pytest.fixture
def bookkeeper_io():
    """Return a BookKeeperIO instance."""
    return BookKeeperIO(user_id=TEST_USERNAME)


def test_constructor():
    """Test the constructor of the BookKeeperIO class."""
    bk = BookKeeperIO(TEST_USERNAME)
    assert isinstance(bk, BookKeeperIO)
    assert bk.user_id == TEST_USERNAME


def test_constructor_missing_args():
    """Test the constructor of the BookKeeperIO class missing username."""
    with pytest.raises(TypeError):
        _ = BookKeeperIO()


# test create_slug


def test_create_slug_basic(bookkeeper_io):
    """Test the create_slug method of the BookKeeperIO class."""
    book = {
        "title": "Test Book",
        "author": "Test Author",
    }

    slug = bookkeeper_io.create_slug(book)

    assert isinstance(slug, str)
    assert slug == "test-author-test-book"


def test_create_slug_special_chars(bookkeeper_io):
    """Test the create_slug method with special characters."""
    book = {
        "title": "A& B: C",
        "author": "!@#$%^",
    }
    slug = bookkeeper_io.create_slug(book)

    assert isinstance(slug, str)
    assert slug == "-a-b-c"


def test_create_slug_with_hyphens(bookkeeper_io):
    """Test the create_slug method with hyphens."""
    book = {
        "title": "The-Hobbit",
        "author": "J.R.R.-Tolkien",
    }
    slug = bookkeeper_io.create_slug(book)

    assert isinstance(slug, str)
    assert slug == "jrr-tolkien-the-hobbit"


def test_create_slug_empty_fields(bookkeeper_io):
    """Test the create_slug method with empty fields."""
    book = {
        "title": "",
        "author": "",
    }
    slug = bookkeeper_io.create_slug(book)

    assert isinstance(slug, str)
    assert slug == "-"


# test _append_book_to_df

# test add_book

# test update_book

# test delete_book

# test revert_deletion_book

# test get_deleted_books

# test get_all_books

# test remove_deleted_books

# test get_books

# test save_books

# test search_user_table

# test get_latest_book_version

# test update_tables

# def test_add_book(bookkeeper_io):
#     book = {
#         "title": "Test Book",
#         "author": "Test Author",
#         "page_current": 10,
#         "finish_date": "2023-10-27",
#     }
#     finished = True

#     # Perform the add_book operation
#     added, book_df = bookkeeper_io.add_book(book, finished, pd.DataFrame())

#     # Assert that the book was added successfully
#     assert added
#     assert len(book_df) == 1
