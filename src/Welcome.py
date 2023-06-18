import streamlit as st
import pandas as pd
from streamlit_lottie import st_lottie
from os import environ

from utils import BookKeeper, load_lottie_url

st.set_page_config(layout="wide")

# lottie_books = load_lottie_url('https://assets3.lottiefiles.com/packages/lf20_1a8dx7zj.json')
lottie_books = load_lottie_url(
    "https://assets3.lottiefiles.com/packages/lf20_4XmSkB.json"
)
st_lottie(lottie_books, speed=1, height=100, key="initial")

bucket = environ.get("BOOKSTORAGE_BUCKET")
bk = BookKeeper("gergokoncz", bucket=bucket)

st.title("BookKeeper")

st.markdown("A simple app to keep track of the books you read and you plan to read.")

st.markdown("## Your stats")

st.session_state.books_df = bk.get_user_books()
st.write(st.session_state.books_df)

if st.button("Save"):
    bk.save_books(st.session_state.books_df)
    st.success("Books saved!")
