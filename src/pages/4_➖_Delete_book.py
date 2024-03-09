#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Delete module of the app.

Delete a book from the collection of books that you maintain.
Also revert the deletion on the day you have done it.
"""

import streamlit as st

from utils import authenticated_with_data

# GLOBALS
DELETE_LOTTIE_URL = "https://assets7.lottiefiles.com/packages/lf20_nux6g0kx.json"


@authenticated_with_data(
    lottie_url=DELETE_LOTTIE_URL,
    title="Delete a book",
    description="Select the book by slug and confirm delete.",
)
def main() -> None:
    """Main flow of the Delete page."""
    selected_slug_for_deletion = st.selectbox(
        "Select book",
        st.session_state.bk.remove_deleted_books(st.session_state.latest_book_state_df)[
            "slug"
        ].unique(),
    )

    if st.button("Delete book"):
        success, st.session_state.today_books_df = st.session_state.bk.delete_book(
            selected_slug_for_deletion,
            st.session_state.today_books_df,
            st.session_state.latest_book_state_df,
        )
        if success:
            saved = st.session_state.bk.save_books(st.session_state.today_books_df)
            if saved:
                st.success("Book deleted!")
                (
                    st.session_state.books_df,
                    st.session_state.today_books_df,
                    st.session_state.latest_book_state_df,
                ) = st.session_state.bk.get_updated_tables()
            else:
                st.error("Something went wrong, please try again.")
        else:
            st.error("Something went wrong, please try again.")

    st.divider()

    st.markdown(
        """
    ## Revert deletion of book
    Select slug from deleted books and revert deletion - can only be done on the same day deletion took place.
    """
    )

    today_books_df = st.session_state.today_books_df
    deleted_books_df = today_books_df.query("deleted==True")

    selected_slug_for_revert = st.selectbox(
        "Select book", deleted_books_df["slug"].unique()
    )

    if st.button("Revert deletion"):
        (
            success,
            st.session_state.today_books_df,
        ) = st.session_state.bk.revert_deletion_book(
            selected_slug_for_revert,
            st.session_state.today_books_df,
        )
        if success:
            saved = st.session_state.bk.save_books(st.session_state.today_books_df)
            if saved:
                st.success("Book deletion reverted!")
                (
                    st.session_state.books_df,
                    st.session_state.today_books_df,
                    st.session_state.latest_book_state_df,
                ) = st.session_state.bk.get_updated_tables()
            else:
                st.error("Something went wrong, please try again.")
        else:
            st.error("Something went wrong, please try again.")


if __name__ == "__main__":
    main()
