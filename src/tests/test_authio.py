#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test module AuthIO."""
import pytest
import yaml
from pytest import fixture
from yaml import SafeLoader

from src.utils import AuthIO

from .conftest import TEST_BUCKET_NAME, TEST_REGION, TEST_USERNAME


@fixture
def test_auth_config():
    """Return a test auth config."""
    with open("tests/test_auth_config.yaml", "r") as f:
        return yaml.load(f, Loader=SafeLoader)


# constructor test
def test_constructor():
    """Test the constructor of the BookKeeperIO class."""
    authio = AuthIO(bucket="bookstorage")

    assert authio.bucket == "bookstorage"
    assert authio.config_filepath == "config/auth_config.yaml"


def test_constructor_lacking_bucket():
    """Test the constructor of the BookKeeperIO class lacking arg."""
    with pytest.raises(TypeError):
        _ = AuthIO()


# test update_auth_config


def test_update_auth_config(test_auth_config):
    """Test the update_auth_config method of the AuthIO class."""
    authio = AuthIO(bucket=TEST_BUCKET_NAME)

    result = authio.update_auth_config(config=test_auth_config)

    assert result is True


# test get_auth_config
@pytest.mark.depends(on=["test_update_auth_config"])
def test_get_auth_config(test_auth_config):
    """
    Test the get_auth_config method of the AuthIO class.

    Given that the config has already been placed in the bucket.
    """
    authio = AuthIO(bucket=TEST_BUCKET_NAME)

    result = authio.get_auth_config()

    assert result == test_auth_config
