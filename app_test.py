import streamlit as st
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import re
#추가
from utils.Scraping import get_naver_news_by_keyword, get_naver_news_by_category

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

def get_search_videos(keyword, max_results=10):
    videos = []
    video_ids_seen = set()  # 중복 방지용
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
                continue  # 중복 제외

            video_duration = item['contentDetails']['duration']

            # duration을 초로 변환
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

    st.markdown("<h1 style='text-align: center;'>🎬 YouTube 영상 분석 플랫폼</h1>", unsafe_allow_html=True)

    #이 두 줄 추가!
    categories = ["인기급상승", "정치", "경제", "사회", "생활/문화", "세계", "IT/과학"]
    selected_category = st.radio("카테고리 선택", categories, horizontal=True)
    
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
                        st.session_state.selected_video_id = video["video_id"]  # 💡 video_id 저장
                        st.switch_page("pages/sel_test.py")

    # 뉴스 출력: 키워드 기반 or 카테고리 기반
    st.markdown("---")
    if keyword:
        st.subheader(f"📰 '{keyword}' 관련 네이버 뉴스")
        news_list = get_naver_news_by_keyword(keyword)
    elif selected_category in ["정치", "경제", "사회", "생활/문화", "세계", "IT/과학"]:
        st.subheader(f"📰 네이버 {selected_category} 뉴스")
        news_list = get_naver_news_by_category(selected_category)
    else:
        news_list = []

    for news in news_list:
        st.markdown(f"<p><a href='{news['url']}' target='_blank'>{news['title']}</a></p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
