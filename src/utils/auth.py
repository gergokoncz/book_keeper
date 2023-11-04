#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Authentication focused module of the app.

With classes and functions related to authentication.
"""
from typing import Any

import boto3
import yaml
from yaml import SafeLoader

s3_client = boto3.client("s3", region_name="eu-north-1")


class AuthIO:
    """Class to handle the IO operations of the authentication."""

    def __init__(self, bucket: str) -> None:
        """Class constructor."""
        self.bucket = bucket
        self.config_filepath = "config/auth_config.yaml"

    def get_auth_config(self) -> dict[str, Any]:
        """
        Get the contents of the authentication file.

        :return: contents of the to the authentication file
        :rtype: dict[str, Any]
        """
        result = s3_client.get_object(Bucket=self.bucket, Key=self.config_filepath)
        return yaml.load(result["Body"], Loader=SafeLoader)

    def update_auth_config(self, config: dict[str, Any]) -> bool:
        """
        Update the authentication file.

        :param auth_file: the path to the authentication file
        :type auth_file: str
        """
        yaml_content = yaml.dump(config, default_flow_style=False)
        try:
            s3_client.put_object(
                Body=yaml_content, Bucket=self.bucket, Key=self.config_filepath
            )
            return True
        except Exception:  # noqa: B902
            return False
