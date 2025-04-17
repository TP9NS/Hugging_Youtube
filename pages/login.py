import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()
REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
REDIRECT_URI = "http://localhost:8501"  # Kakao에 등록된 URI

def show_login_button():
    kakao_login_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={REST_API_KEY}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code"
    )

    st.markdown("### 🧸 카카오 소셜 로그인")
    st.markdown(f"[🔑 카카오로 로그인하기]({kakao_login_url})", unsafe_allow_html=True)
