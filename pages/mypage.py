import streamlit as st
from firebase_admin import db
from PIL import Image
import requests
from io import BytesIO
from utils.Database_CRUD import get_history
from utils.Database_Youtube import get_video_info, get_videos_by_keyword, get_category_channel_recommendations, get_category_mapping
from utils.Recommendation_utils import get_recommendations_by_category_name
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
import html
from collections import defaultdict

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def build_recommendation_graph_data(search_history, watch_history, get_videos_by_keyword, get_category_channel_recommendations, get_video_info, YOUTUBE_API_KEY, category_map):
    from collections import defaultdict
    import html

    search_recommend = defaultdict(list)
    watch_recommend = defaultdict(list)
    rec_sources = defaultdict(lambda: {"search": set(), "watch": set(), "info": None, "category": None})

    seen_keywords = set()
    for record in reversed(search_history):
        kw = record["keyword"]
        if kw in seen_keywords:
            continue
        seen_keywords.add(kw)

        recs = get_videos_by_keyword(kw, YOUTUBE_API_KEY, max_results=5)
        for rec in recs:
            search_recommend[kw].append(rec)
            rec_sources[rec["title"]]["search"].add(kw)
            rec_sources[rec["title"]]["info"] = rec

    used_video_ids = {record["video_id"] for record in watch_history}
    seen_titles = set()
    for record in reversed(watch_history):
        base_video_id = record["video_id"]
        info = get_video_info(base_video_id, YOUTUBE_API_KEY)
        if not info:
            continue

        category_id = info.get("category_id")
        category_name = category_map.get(category_id, "알 수 없음")
        watch_title = info["title"]

        recs = get_recommendations_by_category_name(category_name, YOUTUBE_API_KEY, max_results=10)
        for rec in recs:
            if rec["video_id"] in used_video_ids or rec["title"] in seen_titles:
                continue
            watch_recommend[watch_title].append(rec)
            rec_sources[rec["title"]]["watch"].add(watch_title)
            rec_sources[rec["title"]]["info"] = rec
            rec_sources[rec["title"]]["category"] = category_name
            seen_titles.add(rec["title"])

    return search_recommend, watch_recommend, rec_sources


def create_recommendation_network(search_recommend, watch_recommend, rec_sources):
    G = nx.DiGraph()

    # ✅ 1. 검색 기반 추천
    for keyword, videos in search_recommend.items():
        G.add_node(keyword, label=keyword, color="#FFD93D")
        for video in videos:
            title = video["title"]
            G.add_node(title, label=title, color="#6BCB77", title=f"🔍 추천 출처: '{keyword}' (검색)")
            G.add_edge(keyword, title, title="검색 기반 추천")

    # ✅ 2. 시청 기반 추천 (카테고리 단위로 그룹화)
    category_to_recommendations = defaultdict(set)

    for watched, videos in watch_recommend.items():
        for video in videos:
            title = video["title"]
            category = rec_sources[title].get("category")
            if category:
                category_to_recommendations[category].add(title)

    # ✅ 3. 카테고리 노드 추가 + 해당 추천 영상 연결
    for category_name, title_set in category_to_recommendations.items():
        G.add_node(category_name, label=category_name, color="#4D96FF")  # 🔵 카테고리 노드

        for title in list(title_set)[:10]:  # 최대 10개만
            G.add_node(title, label=title, color="#6BCB77", title=f"👁️ 추천 출처: {category_name} (시청 기반)")
            G.add_edge(category_name, title, title=f"{category_name} 기반 추천")

    # ✅ 4. 고립 노드 처리
    isolated = [n for n in G.nodes if G.degree(n) == 0]
    for node in isolated:
        G.nodes[node]["color"] = "#BBBBBB"
        G.nodes[node]["title"] = G.nodes[node].get("title", "") + "\n❗ 연결된 출처 없음"
        G.nodes[node]["size"] = 10

    return G


def filter_recommendations_connected_in_graph(rec_sources):
    """
    검색, 시청, 카테고리 중 2개 이상의 출처에서 연결된 영상만 필터링
    (즉, 그래프에서 두 개 이상의 노드와 연결된 추천 영상만 포함)
    """
    filtered = []
    for title, source in rec_sources.items():
        search_links = source.get("search", set())
        watch_links = source.get("watch", set())
        category = source.get("category")
        info = source.get("info")

        if not info:
            continue

        total_links = 0
        if search_links:
            total_links += len(search_links)
        if watch_links:
            total_links += len(watch_links)

        # 2개 이상의 출처에서 연결된 경우만 필터링
        if total_links >= 2:
            filtered.append(info)

    return filtered



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
        # ✅ keyword별 count 집계
        keyword_counter = Counter()
        latest_key_map = {}  # 삭제 버튼을 위해 가장 최근 key 저장

        for record in reversed(search_history):
            kw = record["keyword"]
            keyword_counter[kw] += 1
            # 최신 key만 기록 (뒤에서부터 읽고 있으므로 가장 최근 key가 남음)
            if kw not in latest_key_map:
                latest_key_map[kw] = record["key"]

        # ✅ 상위 5개만 추출
        top_keywords = keyword_counter.most_common(5)

        for i, (keyword, count) in enumerate(top_keywords, 1):
            with st.container():
                col1, col2 = st.columns([8, 1])
                with col1:
                    st.markdown(
                        f"""
                        <div style="padding: 10px 15px; background-color: #f9f9f9; border-radius: 10px;">
                            <strong>{i}. {keyword} ({count}회)</strong>
                        </div>
                        """, unsafe_allow_html=True
                    )
                with col2:
                    delete_button = st.button("🗑️", key=f"delete_search_{i}")
                    if delete_button:
                        from utils.Database_CRUD import delete_history_item
                        delete_history_item(user_id, "search_history", latest_key_map[keyword])
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

    # ✅ search_history, watch_history 먼저 가져오고
    search_history = get_history(user_id, "search_history")
    watch_history = get_history(user_id, "watch_history")

    # ✅ 카테고리 ID ↔ 이름 매핑 가져오기
    category_map = get_category_mapping(YOUTUBE_API_KEY)

    # ✅ 추천 데이터 구성
    search_recommend, watch_recommend, rec_sources = build_recommendation_graph_data(
        search_history,
        watch_history,
        get_videos_by_keyword,
        get_category_channel_recommendations,
        get_video_info,
        YOUTUBE_API_KEY,
        category_map  # ✅ 새롭게 전달
    )

    # ✅ 3. 추천이 있는지 여부 체크
    has_search_recs = any(len(v) > 0 for v in search_recommend.values())
    has_watch_recs = any(len(v) > 0 for v in watch_recommend.values())

    # ✅ 4. 네트워크 그래프 시각화
    if has_search_recs or has_watch_recs:
        col1, col2 = st.columns([4, 1])

        with col1:
            st.subheader("📌 추천 영상 네트워크 그래프")

            G = create_recommendation_network(search_recommend, watch_recommend, rec_sources)

            if G.number_of_edges() == 0:
                st.info("연결된 추천 영상이 없어 그래프를 생성하지 않았습니다.")
            else:
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

    st.markdown("---")
    st.subheader("📽️ 추천 영상 목록 (복수 연결 기반)")

    filtered_recommendations = filter_recommendations_connected_in_graph(rec_sources)

    if not filtered_recommendations:
        st.info("추천된 영상이 없습니다.")
    else:
        for video in filtered_recommendations:
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(video['thumbnail'], width=240)
                with col2:
                    st.markdown(f"**📺 {video['title']}**")
                    st.markdown(f"채널명: *{video['channel']}*")
                    st.markdown(f"[▶ 영상 보기](https://youtube.com/watch?v={video['video_id']})")
            st.markdown("---")

main()
