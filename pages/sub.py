import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime
from dotenv import load_dotenv
import os

from utils.summarizer import summarize_video
from utils.analysis import analyze_comments

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

# 쿼리 파라미터로 video_id 받아오기
video_id = st.query_params.get("video_id")
st.write("DEBUG - video_id:", video_id)

if video_id:
    try:
        # 영상 정보 요청
        request = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        response = request.execute()

        if not response["items"]:
            st.error("❌ 영상을 찾을 수 없습니다.")
        else:
            video = response["items"][0]
            title = video["snippet"]["title"]
            thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
            views = int(video["statistics"].get("viewCount", 0))
            likes = int(video["statistics"].get("likeCount", 0))
            published_at = video["snippet"]["publishedAt"]  # 게시 날짜 가져오기

            # ISO 8601 -> YYYY-MM-DD 변환
            published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")

            # 제목, 썸네일, 조회수, 좋아요 출력
            st.markdown(f"## 🎥 {title}")
            st.image(thumbnail, use_column_width=True)
            st.markdown(f"👁️ 조회수: {views:,}회")
            st.markdown(f"👍 좋아요: {likes:,}개")
            st.markdown(f"📅 게시일: {published_date}")
            st.markdown(f"🔗 [YouTube에서 보기](https://www.youtube.com/watch?v={video_id})", unsafe_allow_html=True)

            # 🎯 영상 요약 호출
            st.subheader("📝 영상 요약")
            summary = summarize_video(video_id)
            st.info(summary)

            # 💬 댓글 분석 호출
            st.subheader("💬 댓글 분석")
            df = analyze_comments(video_id)
            st.dataframe(df)

    except Exception as e:
        st.error(f"❗영상 정보를 불러오는 중 오류가 발생했습니다: {e}")
else:
    st.error("❗ video_id가 없습니다.")
