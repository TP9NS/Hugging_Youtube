import streamlit as st
from googleapiclient.discovery import build
from pages.login import show_login_button
from dotenv import load_dotenv
import os
import re
import requests

load_dotenv()  # .env 파일 로드

# YouTube API 설정
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

def get_search_videos(keyword, max_results=10):
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
            pageToken=next_page_token
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

# 메인 앱
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


    st.markdown("<h1 style='text-align: center;'>🎬 YouTube 영상 분석 플랫폼</h1>", unsafe_allow_html=True)

    # 상단 필터 + 검색창
    top_left, top_mid, top_right = st.columns([1, 4, 1])

    with top_left:
        with st.expander("☰ 퀄리티 필터", expanded=False):
            st.markdown("### 🎯 필터 옵션")
            sort_by = st.selectbox("정렬 기준", ["관련도", "업로드 날짜", "조회수"] )
            date_range = st.slider("업로드 기간 (일 기준)", 0, 365, (0, 30))

    with top_mid:
        keyword = st.text_input("🔍 키워드를 입력하세요", "")

    st.markdown("---")

    if keyword:
        st.subheader(f"🔎 '{keyword}' 관련 영상 추천")
        videos = get_search_videos(keyword, 10)
    else:
        st.subheader("🔥 인기 TOP 10 영상 추천")
        videos = get_popular_videos(10)

    # 영상 리스트 출력
    for i in range(0, len(videos), 5):
        cols = st.columns(5)
        for j in range(5):
            if i + j < len(videos):
                video = videos[i + j]
                with cols[j]:
                    st.image(video['thumbnail'], use_container_width=True)
                    if st.button(video["title"], key=video["video_id"]):
                        st.session_state.selected_video_id = video["video_id"]
                        st.switch_page("pages/sel.py")

if __name__ == "__main__":
    main()
