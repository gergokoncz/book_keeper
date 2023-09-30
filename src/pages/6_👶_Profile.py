#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is the contacts page for BookKeeper .

Showing some basic statistics of the books that you have logged.
"""
import streamlit as st


def main() -> None:
    """Main flow of the Profile page."""
    st.set_page_config(
        page_title="BookKeeper", page_icon=":closed_book:", layout="wide"
    )

    st.title("Contact")
    st.divider()
    st.markdown(
        """
                The BookKeeper project is maintaned by a single developer, Gergo Koncz.

                The goal was to get familiar with **streamlit** and to learn how to write a simple web app in **python**.

                My info is listed below.
                If you have any questions, suggestions, or just want to say hi, please feel free to contact me on any of the channels.
                Furthermore, please feel free to submit PRs to the github project.
                """
    )

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**email:**")
        st.markdown("**linkedin:**")
        st.write("**github profile:**")
        st.write("**github project page:**")

    with col2:
        st.write("[koncz.gergo95@gmail.com](mailto:koncz.gergo95@gmail.com)")
        st.write("[Gergo Koncz](https://www.linkedin.com/in/gergo-koncz/)")
        st.write("[gergokoncz](https://github.com/gergokoncz)")
        st.write("[gergokoncz/book_keeper](https://github.com/gergokoncz/book_keeper)")

    st.divider()


if __name__ == "__main__":
    main()
