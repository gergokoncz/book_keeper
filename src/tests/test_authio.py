#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test module AuthIO."""
from pytest import fixture

from src.utils import AuthIO


def test_constructor():
    """Test the constructor of the BookKeeperIO class."""
    authio = AuthIO(bucket="bookstorage")
    assert authio.bucket == "bookstorage"
    assert authio.config_filepath == "config/auth_config.yaml"
