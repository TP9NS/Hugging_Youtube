import streamlit as st
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

# video_id 세션에서 꺼내오기
video_id = st.session_state.get("selected_video_id")
#st.write("DEBUG - video_id:", video_id)

if video_id:
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()

    if not response["items"]:
        st.error("❌ 영상을 찾을 수 없습니다.")
    else:
        video = response["items"][0]
        title = video["snippet"]["title"]
        thumbnail = video["snippet"]["thumbnails"]["high"]["url"]

        # 💡 레이아웃: 왼쪽(썸네일), 오른쪽(설정 폼)
        left, right = st.columns([1, 2])

        with left:
            st.image(thumbnail, use_container_width=True)

        with right:
            st.markdown(f"## 🎥 {title}")
            st.markdown("### ⚙️ 분석 설정을 선택해주세요")

            # 요약 강도 선택 (수정됨)
            summary_strength = st.radio(
                "📝 요약 강도",
                ["짧게", "중간", "길게"],
                horizontal=True
            )

            # 댓글 수 선택
            comment_count = st.slider("💬 댓글 개수", 10, 200, 50, step=10)

            # 분석 시작 버튼
            if st.button("🔍 분석 시작"):
                st.session_state.analysis_settings = {
                    "video_id": video_id,
                    "summary_strength": summary_strength,
                    "comment_count": comment_count
                }
                st.switch_page("pages/sub.py")

else:
    st.error("❗ video_id가 없습니다.")