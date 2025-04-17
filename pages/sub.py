import streamlit as st
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
from datetime import datetime
from utils.KeywordVisualizer import visualize_keywords_from_text

from utils.CommentsGenAI import process_youtube_comments
from utils.CommentsGenAI import *
from utils.TranscriptSummarize import fetch_youtube_transcript, summarize_transcript

import plotly.express as px

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
    st.video(video_url)
    st.markdown(f"👁️ 조회수: {views:,}회")
    st.markdown(f"👍 좋아요: {likes:,}개")
    st.markdown(f"📅 게시일: {published_date}")
    st.markdown(f"🔗 [YouTube에서 보기]({video_url})", unsafe_allow_html=True)

    # 1행 - 영상 요약
    st.subheader("📝 영상 요약")
    transcript = fetch_youtube_transcript(video_url)
    summary = summarize_transcript(transcript, summary_strength=summary_strength)
    st.info(summary)

    # 2행 - 키워드 분석
    st.subheader("🔑 키워드 분석")
    col1, col2 = st.columns(2)

    with col1:
        visualize_keywords_from_text(transcript, chart_type="pie")

    # 3행 - 댓글 요약
    st.subheader("🗣️ 댓글 요약")

    comment_result = process_youtube_comments(API_KEY, video_url, comment_count)

    sentiment = comment_result.get("sentiment_summary", {})
    comment_summary = comment_result.get("summary", "")
    st.info(comment_summary)

    st.subheader("😊 감정 분석")

    # 📋 감정 요약 텍스트
    st.markdown("**📋 감정 요약 텍스트**")
    st.write(sentiment)

    col3, col4 = st.columns(2)
    with col3:

        # 📊 감정 비율 파이 차트
        st.markdown("**📊 감정 비율 파이 차트**")
        labels = list(sentiment.keys())
        values = [int(v.replace('%', '')) for v in sentiment.values()]
        fig = px.pie(
            names=labels,
            values=values,
            title="감정 비율",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        #fig.update_layout(height=300)  # 파이 차트 크기 조절
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❗ 오류 발생: {e}")
