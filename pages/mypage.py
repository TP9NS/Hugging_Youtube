import streamlit as st
from firebase_admin import db
from PIL import Image
import requests
from io import BytesIO
from utils.Database_CRUD import get_history

def main():
    st.title("👤 마이페이지")

    user_info = st.session_state.get("user_info", {})
    user_id = st.session_state.get("user_id", None)

    if not user_id:
        st.warning("로그인이 필요합니다.")
        return

    # 📌 카카오 프로필 정보 출력
    nickname = user_info.get("properties", {}).get("nickname", "알 수 없음")
    profile_img_url = user_info.get("properties", {}).get("profile_image")

    col1, col2 = st.columns([1, 3])
    with col1:
        if profile_img_url:
            try:
                response = requests.get(profile_img_url)
                img = Image.open(BytesIO(response.content))
                st.image(img, caption="프로필", use_container_width=True)
            except:
                st.info("프로필 이미지 불러오기 실패")
        else:
            st.info("프로필 이미지 없음")
    with col2:
        st.markdown(f"**닉네임:** `{nickname}`")
        st.markdown(f"**Kakao ID:** `{user_id}`")

    st.markdown("---")

    # 🔍 검색 기록 불러오기
    st.subheader("🔎 검색 기록")
    search_history = get_history(user_id, "search_history")
    if search_history:
        for i, record in enumerate(reversed(search_history), 1):
            st.markdown(f"- {i}. `{record['keyword']}`")
    else:
        st.info("검색 기록이 없습니다.")

    # 📺 시청 기록 불러오기
    st.subheader("📺 시청 기록 (Video ID)")
    watch_history = get_history(user_id, "watch_history")
    if watch_history:
        for i, record in enumerate(reversed(watch_history), 1):
            video_id = record["video_id"]
            st.markdown(f"- {i}. [https://youtube.com/watch?v={video_id}](https://youtube.com/watch?v={video_id})")
    else:
        st.info("시청 기록이 없습니다.")


main()
