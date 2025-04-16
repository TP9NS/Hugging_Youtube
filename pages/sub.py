import streamlit as st
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
from datetime import datetime

from utils.CommentsAnalysis import process_youtube_comments
from utils.CommentsGenAI import *
from utils.TranscriptSummarize import fetch_youtube_transcript, summarize_transcript

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")  # OpenAI / Gemini용
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # YouTube Data API용

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

settings = st.session_state.get("analysis_settings", {})
video_id = settings.get("video_id")
summary_strength = settings.get("summary_strength", "중간")
comment_count = settings.get("comment_count", 30)

if not video_id:
    st.error("❌ 영상 정보가 없습니다.")
    st.stop()

# 유튜브 영상 정보 가져오기
try:
    response = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    ).execute()

    if not response["items"]:
        st.error("❌ 영상을 찾을 수 없습니다.")
        st.stop()

    video = response["items"][0]
    title = video["snippet"]["title"]
    thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
    views = int(video["statistics"].get("viewCount", 0))
    likes = int(video["statistics"].get("likeCount", 0))
    published_at = video["snippet"]["publishedAt"]
    published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    # 제목, 썸네일, 통계
    st.markdown(f"## 🎥 {title}")
    st.image(thumbnail, use_column_width=True)
    st.markdown(f"👁️ 조회수: {views:,}회")
    st.markdown(f"👍 좋아요: {likes:,}개")
    st.markdown(f"📅 게시일: {published_date}")
    st.markdown(f"🔗 [YouTube에서 보기]({video_url})", unsafe_allow_html=True)

    # 🔹 요약
    st.subheader("📝 영상 요약")
    transcript = fetch_youtube_transcript(video_url)
    summary = summarize_transcript(transcript, summary_strength=summary_strength)
    st.info(summary)

    # 🔸 댓글 분석
    st.subheader("💬 댓글 분석")
    comment_result = process_youtube_comments(API_KEY, video_url, max_comments=comment_count)

    sentiment = comment_result.get("sentiment_summary", {})
    comment_summary = comment_result.get("summary", "")

    # 감정 요약 출력
    st.markdown("**😊 감정 요약:**")
    st.write(sentiment)

    # 댓글 요약 출력
    st.markdown("**🗣️ 요약 내용:**")
    st.info(comment_summary)

except Exception as e:
    st.error(f"❗ 오류 발생: {e}")
