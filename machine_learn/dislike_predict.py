import re
import os
import pandas as pd
import numpy as np
import joblib
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

# 모델과 feature column 불러오기
model = joblib.load("machine_learn/dislike_predictor_rf_with_view.pkl")
feature_columns = joblib.load("machine_learn/feature_columns_rf_with_view.pkl")

# 유튜브 링크에서 video_id 추출
def extract_video_id(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

# YouTube API로 영상 정보 가져오기
def get_video_features(video_id: str):
    request = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    )
    response = request.execute()

    if not response["items"]:
        return None

    info = response["items"][0]
    category_id = info["snippet"]["categoryId"]
    stats = info["statistics"]

    return {
        "categoryId": category_id,
        "view_count": int(stats.get("viewCount", 0)),
        "likes": int(stats.get("likeCount", 0)),
        "comment_count": int(stats.get("commentCount", 0))
    }

# 전체 예측 함수
def predict_dislikes_from_link(video_url: str) -> str:
    video_id = extract_video_id(video_url)
    if not video_id:
        return "❌ 유효하지 않은 YouTube 링크입니다."

    features = get_video_features(video_id)
    if not features:
        return "❌ 영상 정보를 가져오지 못했습니다."

    category = features["categoryId"]
    views = features["view_count"]
    likes = features["likes"]
    comment_count = features["comment_count"]

    # ✅ 로그 변환 및 파생 피처
    view_log = np.log1p(views)
    likes_log = np.log1p(likes)
    comment_log = np.log1p(comment_count)
    like_comment_ratio = likes / (comment_count + 1)

    # 입력값 구성
    input_dict = {
        "view_log": [view_log],
        "likes_log": [likes_log],
        "comment_log": [comment_log],
        "like_comment_ratio": [like_comment_ratio]
    }

    # ✅ 카테고리 원핫 인코딩
    for col in feature_columns:
        if col.startswith("categoryId_"):
            input_dict[col] = [1 if col == f"categoryId_{category}" else 0]

    input_df = pd.DataFrame(input_dict)

    # 누락된 컬럼은 0으로 채움
    for col in feature_columns:
        if col not in input_df.columns:
            input_df[col] = 0
    input_df = input_df[feature_columns]

    # 예측
    prediction = model.predict(input_df)[0]
    return f"📊 예측된 싫어요 수: {int(prediction):,}개"
