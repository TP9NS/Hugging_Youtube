import streamlit as st
from googleapiclient.discovery import build
from pages.login import show_login_button
from dotenv import load_dotenv
import os
import re
import requests
from datetime import datetime, timedelta
from utils.Database_CRUD import save_search, save_watch_history
from utils.Scraping import get_naver_news_by_keyword, get_naver_news_by_category

# .env 파일 로드
load_dotenv() 

API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=API_KEY)

# 🔐 카카오 인증 코드로 access_token 요청
def get_kakao_token(code):
    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": os.getenv("KAKAO_REST_API_KEY"),
        "redirect_uri": "http://localhost:8501",
        "code": code
    }
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        st.error("❌ access_token 요청 실패")
        st.write(response.text)
        return None

# 🔐 access_token으로 사용자 정보 요청
def get_kakao_user_info(access_token):
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(user_info_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("❌ 사용자 정보 요청 실패")
        st.write(response.text)
        return None

# 인기 영상 가져오기
def get_popular_videos(max_results=6):
    request = youtube.videos().list(
        part='snippet',
        chart='mostPopular',
        regionCode='KR',
        maxResults=max_results
    )
    response = request.execute()
    videos = []
    for item in response['items']:
        videos.append({
            'title': item['snippet']['title'],
            'video_id': item['id'],
            'thumbnail': item['snippet']['thumbnails']['medium']['url']
        })
    return videos

# 검색 영상 가져오기
def get_search_videos(keyword, max_results=10, order="relevance", start_date=None):
    videos = []
    video_ids_seen = set()
    next_page_token = None

    while len(videos) < max_results:
        search_request = youtube.search().list(
            part='snippet',
            q=keyword,
            type='video',
            regionCode='KR',
            maxResults=25,
            pageToken=next_page_token,
            order=order
        )
        search_response = search_request.execute()
        video_ids = [item['id']['videoId'] for item in search_response['items']]
        next_page_token = search_response.get("nextPageToken")

        details_request = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(video_ids)
        )
        details_response = details_request.execute()

        for item in details_response['items']:
            vid = item['id']
            if vid in video_ids_seen:
                continue

            video_duration = item['contentDetails']['duration']
            match = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", video_duration)
            minutes = int(match.group(1)) if match and match.group(1) else 0
            seconds = int(match.group(2)) if match and match.group(2) else 0
            duration_seconds = minutes * 60 + seconds

            published_at_str = item['snippet']['publishedAt']
            published_at = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ")
            if start_date and published_at < start_date:
                continue

            if duration_seconds > 60:
                videos.append({
                    'title': item['snippet']['title'],
                    'video_id': vid,
                    'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                    'views': int(item['statistics'].get('viewCount', 0))
                })
                video_ids_seen.add(vid)

            if len(videos) >= max_results:
                break

        if not next_page_token:
            break

    return videos

#메인 앱
def main():
    st.set_page_config(
        page_title="YouTube 영상 분석",
        page_icon="🎥",
        layout="wide"
    )

    if "code" not in st.session_state:
        query_params = st.query_params
        code = query_params.get("code")
        if not code or code == "_":
            show_login_button()
            return
        st.session_state.code = code
    else:
        code = st.session_state.code

    if "access_token" not in st.session_state:
        access_token = get_kakao_token(code)
        if not access_token:
            return
        st.session_state.access_token = access_token
    else:
        access_token = st.session_state.access_token

    if "user_info" not in st.session_state:
        user_info = get_kakao_user_info(access_token)
        if not user_info:
            return
        st.session_state.user_info = user_info
        st.session_state.user_id = user_info.get("id")
    else:
        user_info = st.session_state.user_info

    # 1행: 마이페이지
    with st.container():
        row1_col1, row1_col2, row1_col3 = st.columns([6, 1, 1])
        with row1_col3:
            st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
            if st.button("👤 마이페이지"):
                st.switch_page("pages/mypage.py")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>🎬 YouTube 영상 분석 플랫폼</h1>", unsafe_allow_html=True)

    # 2행: 키워드 입력창
    with st.container():
        row2_col1, row2_col2, row2_col3 = st.columns([1, 6, 1])
        with row2_col2:
            keyword = st.text_input("🔍 키워드를 입력하세요", "")

    st.markdown("---")

    # 3행: 카테고리 왼쪽, 퀄리티 필터 오른쪽
    with st.container():
        row3_col1, row3_col2, row3_col3 = st.columns([6, 0.5, 1.5])

        with row3_col1:
            categories = ["인기급상승", "정치", "경제", "사회", "생활/문화", "세계", "IT/과학"]
            selected_category = st.radio("📂 카테고리 선택", categories, horizontal=True)

        with row3_col3:
            with st.expander("🎯 퀄리티 필터", expanded=False):
                sort_by = st.selectbox("정렬 기준", ["관련도", "업로드 날짜", "조회수"], key="sort_selectbox")
                date_options = ["전체", "오늘", "이번 주", "이번 달", "올해"]
                selected_period = st.selectbox("업로드 기간", date_options, key="date_selectbox")

    order_map = {
        "관련도": "relevance",
        "업로드 날짜": "date",
        "조회수": "viewCount"
    }
    order_value = order_map.get(sort_by, "relevance")

    today = datetime.now()
    period_map = {
        "오늘": today - timedelta(days=1),
        "이번 주": today - timedelta(days=today.weekday()),
        "이번 달": today.replace(day=1),
        "올해": today.replace(month=1, day=1)
    }
    start_date = period_map.get(selected_period) if selected_period != "전체" else None

    if keyword:
        st.subheader(f"🔎 '{keyword}' 관련 영상 추천")
        videos = get_search_videos(keyword, 10, order=order_value, start_date=start_date)
        save_search(st.session_state.user_id, keyword)
    else:
        st.subheader("🔥 인기 TOP 10 영상 추천")
        videos = get_popular_videos(10)

    for i in range(0, len(videos), 5):
        cols = st.columns(5)
        for j in range(5):
            if i + j < len(videos):
                video = videos[i + j]
                with cols[j]:
                    st.image(video['thumbnail'], use_container_width=True)
                    if st.button(video["title"], key=video["video_id"]):
                        st.session_state.selected_video_id = video["video_id"]
                        save_watch_history(st.session_state.user_id, video["video_id"])
                        st.switch_page("pages/sel.py")

    st.markdown("---")
    if keyword:
        st.subheader(f"📰 '{keyword}' 관련 네이버 뉴스")
        news_list = get_naver_news_by_keyword(keyword)
    elif selected_category in ["정치", "경제", "사회", "생활/문화", "세계", "IT/과학"]:
        st.subheader(f"📰 네이버 {selected_category} 뉴스")
        news_list = get_naver_news_by_category(selected_category)
    else:
        news_list = []

    if not news_list:
        st.info("📭 뉴스가 없습니다.")
    else:
        for news in news_list:
            st.markdown(
                f"""
                <div style="
                    display: flex;
                    align-items: center;
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    padding: 12px 16px;
                    margin-bottom: 10px;
                    background-color: #f9f9f9;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                ">
                    {'<img src="' + news['thumbnail'] + '" style="width: 100px; height: auto; margin-right: 16px; border-radius: 8px;">' if news.get('thumbnail') else ''}
                    <div>
                        <a href="{news['url']}" target="_blank" style="text-decoration: none; color: #222;">
                            <h4 style="margin: 0; font-size: 17px;">{news['title']}</h4>
                        </a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
if __name__ == "__main__":
    main()