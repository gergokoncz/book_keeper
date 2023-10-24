#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test module BookKeeperIO."""

import pytest
from pytest import fixture

from src.utils import BookKeeperIO


def test_constructor():
    """Test the constructor of the BookKeeperIO class."""
    bk = BookKeeperIO("gergokoncz", bucket="bookstorage")
    assert isinstance(bk, BookKeeperIO)
    assert bk.user_id == "gergokoncz"
    assert bk.bucket == "bookstorage"


def test_constructor_missing_args():
    """Test the constructor of the BookKeeperIO class missing username."""
    with pytest.raises(TypeError):
        _ = BookKeeperIO(bucket="bookstorage")
