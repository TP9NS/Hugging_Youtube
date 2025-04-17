import streamlit as st
from firebase_admin import db
from PIL import Image
import requests
from io import BytesIO
from utils.Database_CRUD import get_history
from utils.Database_Youtube import get_video_info,get_videos_by_keyword, get_category_channel_recommendations, get_top_recommendations_from_watch_history,analyze_watch_history_similarity
from pages.login import show_login_button
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
from collections import Counter, defaultdict

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def main():
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🏠 메인으로", key="go_main"):
            st.switch_page("app.py")
    st.title("👤 마이페이지")

    user_info = st.session_state.get("user_info", {})
    user_id = st.session_state.get("user_id", None)

    if not user_id:
        st.warning("로그인이 필요합니다.")
        show_login_button()
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
    st.subheader("🔎 검색 기록")

    search_history = get_history(user_id, "search_history")

    if search_history:
        for i, record in enumerate(reversed(search_history), 1):
            with st.container():
                col1, col2 = st.columns([8, 1])
                with col1:
                    st.markdown(
                        f"""
                        <div style="padding: 10px 15px; background-color: #f9f9f9; border-radius: 10px;">
                             <strong>{i}. {record['keyword']}</strong>
                        </div>
                        """, unsafe_allow_html=True
                    )
                with col2:
                    delete_button = st.button("🗑️", key=f"delete_search_{i}")
                    if delete_button:
                        from utils.Database_CRUD import delete_history_item
                        delete_history_item(user_id, "search_history", record["key"])
                        st.rerun()
    else:
        st.info("검색 기록이 없습니다.")

    st.subheader("📺 시청 기록")
    watch_history = get_history(user_id, "watch_history")

    if watch_history:
        for i, record in enumerate(reversed(watch_history), 1):
            video_id = record["video_id"]
            video_info = get_video_info(video_id, YOUTUBE_API_KEY)

            if video_info:
                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        st.image(video_info["thumbnail"], width=220)
                    with col2:
                        st.markdown(f"**📺 {video_info['title']}**")
                        st.markdown(f"채널명: *{video_info['channel']}*")
                        st.markdown(f"[▶ 영상 보기](https://youtube.com/watch?v={video_id})")
                    with col3:
                        delete_button = st.button("🗑️", key=f"delete_watch_{i}")
                        if delete_button:
                            from utils.Database_CRUD import delete_history_item
                            delete_history_item(user_id, "watch_history", record["key"])
                            st.rerun()
    else:
        st.info("시청 기록이 없습니다.")


    st.markdown("---")
    st.subheader("🎯 검색 기록 기반 추천 영상")

    search_history = get_history(user_id, "search_history")

    if search_history:
        # 중복 제거된 키워드 리스트 생성
        keywords = []
        seen = set()
        for record in reversed(search_history):
            kw = record["keyword"]
            if kw not in seen:
                keywords.append(kw)
                seen.add(kw)

        for keyword in keywords:
            st.markdown(f"#### 🔍 `{keyword}` 관련 영상 추천")
            recommended = get_videos_by_keyword(keyword, max_results=1)

            for video in recommended:
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(video['thumbnail'], width=240)
                    with col2:
                        st.markdown(f"**📺 {video['title']}**")
                        st.markdown(f"채널명: *{video['channel']}*")
                        st.markdown(f"[▶ 영상 보기](https://youtube.com/watch?v={video['video_id']})")
    else:
        st.info("검색 기록이 없습니다.")

    st.markdown("---")
    st.subheader("🎯 시청 기록 기반 추천 영상")

    if watch_history:
        # ✔ Step 1. TF-IDF 유사도 배열을 구현
        similar_pairs = analyze_watch_history_similarity(watch_history, YOUTUBE_API_KEY)
        filtered_pairs = [(v1, v2, s) for (v1, v2, s) in similar_pairs if s >= 0.1]

        # 기준이 된 시청 영상이 중복되지 않게 관리
        used_base_videos = set()
        recommended = {}

        for vid1, vid2, score in filtered_pairs:
            for base_vid in [vid1, vid2]:
                if base_vid in used_base_videos:
                    continue  # 중복된 기준 영상은 건너뜀
                used_base_videos.add(base_vid)

                info = get_video_info(base_vid, YOUTUBE_API_KEY)
                if not info:
                    continue
                keyword = info["title"].split(" ")[0]
                base_title = info["title"]

                results = get_videos_by_keyword(keyword, max_results=5)
                for video in results:
                    if video["video_id"] in used_base_videos:
                        continue
                    if video["video_id"] not in recommended:
                        recommended[video["video_id"]] = (video, [(base_title, score)])
                    else:
                        recommended[video["video_id"]][1].append((base_title, score))

                    if len(recommended) >= 3:
                        break
                if len(recommended) >= 3:
                    break
            if len(recommended) >= 3:
                break

        # ✔ Step 3. 추천 결과 표시
        if recommended:
            for video_id, (video, base_infos) in recommended.items():
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(video["thumbnail"], width=240)
                    with col2:
                        st.markdown(f"**📺 {video['title']}**")
                        st.markdown(f"채널명: *{video['channel']}*")
                        st.markdown(f"[▶ 영상 보기](https://youtube.com/watch?v={video['video_id']})")

                        for base_title, score in base_infos:
                            st.markdown(f"⟷ **{base_title}** 와의 유사도: `{score}`")
                st.markdown("---")
        else:
            st.info("유사도 기반 추천 영상이 없습니다.")
    else:
        st.info("시청 기록이 없습니다.")

main()
