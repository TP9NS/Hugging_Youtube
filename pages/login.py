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

    st.markdown(
        """
        <div style="text-align: center; padding: 2rem 1rem;">
            <h1>🎥 YouTube 감정 분석 플랫폼</h1>
            <p style="font-size: 1.1rem; color: #444;">
                AI로 유튜브 댓글을 분석하고, 영상 반응을 요약해보세요!<br>
                <b>검색 기록</b>과 <b>시청 기록</b>을 저장하고 마이페이지에서 확인할 수 있습니다.
            </p>
            <p style="font-size: 1rem; color: #777; margin-top: 1rem;">
                👉 먼저 <b>카카오 로그인</b>을 해주세요!
            </p>
            <a href="{0}" target="_self">
                <button style="
                    background-color: #FEE500;
                    color: #191600;
                    border: none;
                    padding: 0.8rem 1.6rem;
                    font-size: 1.1rem;
                    font-weight: bold;
                    border-radius: 8px;
                    cursor: pointer;
                    margin-top: 1.2rem;
                ">
                    🔐 카카오로 로그인
                </button>
            </a>
        </div>
        """.format(kakao_login_url),
        unsafe_allow_html=True
    )
