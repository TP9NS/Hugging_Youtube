import streamlit as st
from firebase_admin import db
from PIL import Image
import requests
from io import BytesIO
from utils.Database_CRUD import get_history
from utils.Database_Youtube import get_video_info,get_videos_by_keyword, get_category_channel_recommendations
from pages.login import show_login_button
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
from collections import Counter
import matplotlib.pyplot as plt
from pyvis.network import Network
import streamlit as st
import tempfile
import networkx as nx


load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# 📌 함수 정의: 시청/검색 기록 기반 추천 데이터 구성
def build_recommendation_graph_data(search_history, watch_history, get_videos_by_keyword, get_category_channel_recommendations, YOUTUBE_API_KEY):
    from collections import Counter
    search_recommend = {}
    watch_recommend = {}

    seen_keywords = set()
    for record in reversed(search_history):
        kw = record["keyword"]
        if kw in seen_keywords:
            continue
        seen_keywords.add(kw)
        recs = get_videos_by_keyword(kw, max_results=1)
        search_recommend[kw] = [rec["title"] for rec in recs]

    used_video_ids = {record["video_id"] for record in watch_history}
    seen_titles = set()
    for record in reversed(watch_history):
        base_video_id = record["video_id"]
        recs = get_category_channel_recommendations(base_video_id, YOUTUBE_API_KEY, max_results=3)

        info = get_video_info(base_video_id, YOUTUBE_API_KEY)
        if not info:
            continue
        watch_title = info["title"]
        watch_recommend[watch_title] = []

        for rec in recs:
            if rec["video_id"] in used_video_ids or rec["title"] in seen_titles:
                continue
            watch_recommend[watch_title].append(rec["title"])
            seen_titles.add(rec["title"])

        if len(watch_recommend) >= 6:
            break

    return search_recommend, watch_recommend

# 📌 함수 정의: 그래프 객체 생성
def create_recommendation_network(search_recommend, watch_recommend):
    G = nx.DiGraph()

    # 검색 기반 추천
    for keyword, videos in search_recommend.items():
        G.add_node(keyword, label=keyword, color="#FFD93D")  # 노란색 (검색 키워드)
        for video in videos:
            G.add_node(
                video,
                label=video,
                color="#6BCB77",  # 초록색 (추천 영상)
                title=f"🔍 추천 출처: '{keyword}' (검색)"
            )
            G.add_edge(keyword, video, title="검색 기반 추천")

    # 시청 기반 추천
    for watched, recs in watch_recommend.items():
        G.add_node(watched, label=watched, color="#4D96FF")  # 파란색 (시청 영상)
        for video in recs:
            G.add_node(
                video,
                label=video,
                color="#6BCB77",  # 초록색 (추천 영상)
                title=f"👁️ 추천 출처: '{watched}' (시청)"
            )
            G.add_edge(watched, video, title="시청 기반 추천")

    # 고립 노드 스타일 변경
    isolated = [node for node in G.nodes if G.degree(node) == 0]
    for node in isolated:
        G.nodes[node]["color"] = "#BBBBBB"  # 회색
        G.nodes[node]["title"] = G.nodes[node].get("title", "") + "\n❗ 연결된 출처 없음"
        G.nodes[node]["size"] = 10  # 작게 표시

    return G


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
                    col1, col2, col3 = st.columns([1, 5, 1])
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
        used_video_ids = {record["video_id"] for record in watch_history}
        recommended_videos = []
        seen_titles = set()

        # 시청 기록 순회 (최신 → 오래된 순으로)
        for record in reversed(watch_history):
            base_video_id = record["video_id"]

            recs = get_category_channel_recommendations(base_video_id, YOUTUBE_API_KEY, max_results=3)
            for rec in recs:
                if rec["video_id"] in used_video_ids:
                    continue
                if rec["title"] in seen_titles:
                    continue  # 같은 제목의 중복 방지

                recommended_videos.append({
                    "from_video_id": base_video_id,
                    "recommended": rec
                })
                seen_titles.add(rec["title"])

            # 너무 많으면 자르기 (예: 상위 6개까지만)
            if len(recommended_videos) >= 6:
                break

        if recommended_videos:
            for rec_block in recommended_videos:
                base_video_id = rec_block["from_video_id"]
                rec = rec_block["recommended"]
                info = get_video_info(base_video_id, YOUTUBE_API_KEY)

                st.markdown(f"#### 🔁 `{info['title']}` 기반 추천")
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(rec['thumbnail'], width=240)
                    with col2:
                        st.markdown(f"**📺 {rec['title']}**")
                        st.markdown(f"채널명: *{rec['channel']}*")
                        st.markdown(f"[▶ 영상 보기](https://youtube.com/watch?v={rec['video_id']})")

                st.markdown("---")
        else:
            st.info("추천할 영상이 없습니다.")
    else:
        st.info("시청 기록이 없습니다.")

    # 2단 컬럼 구성: 좌측 = 그래프, 우측 = 설명
    col1, col2 = st.columns([4, 1])

    with col1:
        st.subheader("📌 추천 영상 네트워크 그래프")

        search_recommend, watch_recommend = build_recommendation_graph_data(
            search_history,
            watch_history,
            get_videos_by_keyword,
            get_category_channel_recommendations,
            YOUTUBE_API_KEY
        )

        G = create_recommendation_network(search_recommend, watch_recommend)

        net = Network(height="550px", width="100%", directed=True)
        net.from_nx(G)
        net.repulsion(node_distance=200, spring_length=200)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
            path = tmp_file.name
            net.save_graph(path)

        st.components.v1.html(open(path, "r", encoding="utf-8").read(), height=600)

    with col2:
        st.markdown("### 🧾 Label")
        st.markdown("""
        <div style="line-height: 2;">
        🟡 <b>검색 키워드</b><br>
        🔵 <b>시청한 영상</b><br>
        🟢 <b>추천된 영상</b><br>
        ⚪ <b>고립된 추천 영상</b> (연결 없음)
        </div>
        """, unsafe_allow_html=True)

main()
