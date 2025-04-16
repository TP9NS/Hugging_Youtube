import streamlit as st
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import re

load_dotenv()  # .env 파일 로드

# YouTube API 설정
API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=API_KEY)

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

# 키워드 기반 영상 검색
def get_search_videos(keyword, max_results=6):
    # 검색 API로 영상 ID 목록 가져오기
    search_request = youtube.search().list(
        part='snippet',
        q=keyword,
        type='video',
        regionCode='KR',
        maxResults=max_results
    )
    search_response = search_request.execute()
    
    video_ids = [item['id']['videoId'] for item in search_response['items']]
    
    # 상세 정보 (조회수 포함) 가져오기
    details_request = youtube.videos().list(
        part='snippet,statistics,contentDetails',
        id=','.join(video_ids)
    )
    details_response = details_request.execute()

    videos = []
    for item in details_response['items']:
        # 영상 길이를 확인
        video_duration = item['contentDetails']['duration']

        # 영상 길이를 분과 초로 분해
        duration_seconds = 0
        match = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", video_duration)
        if match:
            minutes = match.group(1)
            seconds = match.group(2)

            if minutes:
                duration_seconds += int(minutes) * 60  # 분을 초로 변환
            if seconds:
                duration_seconds += int(seconds)  # 초 추가

        # 1분 이하(60초 이하) 영상을 제외
        if duration_seconds <= 60:
            continue

        videos.append({
            'title': item['snippet']['title'],
            'video_id': item['id'],
            'thumbnail': item['snippet']['thumbnails']['medium']['url'],
            'views': int(item['statistics'].get('viewCount', 0))
        })
    
    return videos

# 메인 앱
def main():
    st.set_page_config(
        page_title="YouTube 영상 분석",
        page_icon="🎥",
        layout="wide"
    )

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

    # 3개씩 출력
    for i in range(0, len(videos), 5):
        cols = st.columns(5)
        for j in range(5):
            if i + j < len(videos):
                video = videos[i + j]
                with cols[j]:
                    st.image(video['thumbnail'], use_column_width=True)
                    st.markdown(
                        f"<h5 style='margin-bottom:5px;'><a href='/sub?video_id={video['video_id']}' target='_self'>{video['title']}</a></h5>",
                        unsafe_allow_html=True
                    )

if __name__ == "__main__":
    main()
