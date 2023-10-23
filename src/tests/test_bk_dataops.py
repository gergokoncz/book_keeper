#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test module BookKeeperDataOps."""

from pytest import fixture

from src.utils import BookKeeperDataOps


def test_constructor():
    """Test the constructor of the BookKeeperIO class."""
    bk_dops = BookKeeperDataOps()
    assert isinstance(bk_dops, BookKeeperDataOps)
