#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This is the utility class of the app. With classes and functions for UI components."""

from functools import wraps
from os import environ

import streamlit as st
import streamlit_authenticator as stauth
from streamlit_lottie import st_lottie

from .auth import AuthIO
from .bk_io import BookKeeperIO
from .utils import load_lottie_asset

EXAMPLE_LOTTIE_URL = "https://assets3.lottiefiles.com/packages/lf20_4XmSkB.json"


def base_layout(
    lottie_url: str = EXAMPLE_LOTTIE_URL,
    title="BookKeeper",
    description="Keep track of the books you read or you plan to read.",
):
    """Decorator to set the base layout of the pages."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ## CONFIG
            st.set_page_config(
                page_title="BookKeeper", page_icon=":closed_book:", layout="wide"
            )

            lottie_file = load_lottie_asset(lottie_url)
            st_lottie(lottie_file, speed=1, height=100, key="initial")

            st.title(title)

            st.markdown(description)

            st.divider()

            return func(*args, **kwargs)

        return wrapper

    return decorator


def with_authentication(func):
    """Decorator to authenticate the user and load the data."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # AUTH
        authio = AuthIO(bucket=environ.get("BOOKSTORAGE_BUCKET"))
        config = authio.get_auth_config()

        authenticator = stauth.Authenticate(
            config["credentials"],
            config["cookie"]["name"],
            config["cookie"]["key"],
            config["cookie"]["expiry_days"],
            config["preauthorized"],
        )

        authenticator.login("Login", "main")
        # Present content based on authentication status
        ## If user is authenticated, show the app
        if st.session_state["authentication_status"]:
            authenticator.logout("Logout", "sidebar")

            return func(*args, **kwargs)

        ## If user gave wrong credentials
        elif st.session_state["authentication_status"] is False:
            st.error("Username/password is incorrect")

        ## If user has not logged in yet
        elif st.session_state["authentication_status"] is None:
            st.warning("Please enter your username and password")

            # enable registration
            if st.checkbox("New user?"):
                try:
                    if authenticator.register_user(
                        "Register user", "main", preauthorization=False
                    ):
                        authio.update_auth_config(config)
                        st.success("You have successfully registered!")
                except Exception as e:  # noqa: B902
                    st.error(e)

    return wrapper


def with_user_logs(func):
    """Decorator to add user logs to the page."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with st.spinner("Your books are loading..."):
            if "bk" not in st.session_state:
                st.session_state.bk = BookKeeperIO(st.session_state["username"])

            # get an update on the tables
            if "books_df" not in st.session_state:
                (
                    st.session_state.books_df,
                    st.session_state.today_books_df,
                    st.session_state.latest_book_state_df,
                ) = st.session_state.bk.get_updated_tables()

        # here comes the func
        return func(*args, **kwargs)

    return wrapper
