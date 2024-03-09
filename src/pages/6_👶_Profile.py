#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is the profile page for BookKeeper .

Enables you to change user details, except username.
"""

from os import environ

import streamlit as st
import streamlit_authenticator as stauth

from utils import AuthIO, base_layout

# VARS
PROFILE_LOTTIE_URL = (
    "https://lottie.host/850fc636-eca1-4080-ba93-8bf228a95437/ZadfNJek3L.json"
)


@base_layout(
    lottie_url=PROFILE_LOTTIE_URL,
    title="Your profile",
    description="Change your user details and reset your password.",
)
def main() -> None:
    """Main flow of the Profile page."""
    ## AUTH
    bucket = environ.get("BOOKSTORAGE_BUCKET")
    authio = AuthIO(bucket=bucket)
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
        # modify user details
        try:
            if authenticator.update_user_details(
                st.session_state["username"], "Update user details"
            ):
                authio.update_auth_config(config)
                st.success("You have successfully updated your details!")
        except Exception as e:  # noqa: B902
            st.error(e)

        # reset password
        try:
            if authenticator.reset_password(
                st.session_state["username"], "Reset password"
            ):
                authio.update_auth_config(config)
                st.success("You have successfully reset your password!")
        except Exception as e:  # noqa: B902
            st.error(e)

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


if __name__ == "__main__":
    main()
