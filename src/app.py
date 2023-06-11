import streamlit as st
import requests
from streamlit_lottie import st_lottie

from utils import get_user_books


def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()

lottie_books = load_lottie_url('https://assets3.lottiefiles.com/packages/lf20_1a8dx7zj.json')
st_lottie(lottie_books, speed=1, height=100, key="initial")

st.title("BookKeeper")

st.markdown("A simple app to keep track of the books you read and you plan to read.")

st.markdown("## Your stats")

st.session_state.books_df = get_user_books("user1")
st.write(st.session_state.books_df)