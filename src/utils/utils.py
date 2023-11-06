#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The utility class of the app.

With classes and functions for IO and data manipulation.
"""

from typing import Optional

import requests


def load_lottie_url(url: str) -> Optional[dict]:
    """
    Load the lottie file located at given url.

    :param url: the url to load
    :type url: str

    :return: the lottie file if request was successful
    :rtype: Optional[dict]
    """
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
