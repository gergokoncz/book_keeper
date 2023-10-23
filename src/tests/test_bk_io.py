#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test module BookKeeperIO."""

from pytest import fixture

from src.utils import BookKeeperIO


def test_constructor():
    """Test the constructor of the BookKeeperIO class."""
    bk = BookKeeperIO("gergokoncz", bucket="bookstorage")
    assert bk.user_id == "gergokoncz"
    assert bk.bucket == "bookstorage"
