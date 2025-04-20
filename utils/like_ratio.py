import pandas as pd
from googleapiclient.discovery import build
import os

# 평균 좋아요 비율 계산
def get_average_like_ratio():
    try:
        # CSV 파일 불러오기
        df = pd.read_csv("kaggle_dataset_KR/KR_youtube_trending_data.csv")

        # view_count가 0인 행 제거
        df = df[df['view_count'] != 0]

        # like_ratio 계산
        df['like_ratio'] = df['likes'] / df['view_count']

        # 평균 계산 (NaN 방지)
        avg_like_ratio = df['like_ratio'].mean()

        if pd.isna(avg_like_ratio) or avg_like_ratio == 0:
            print("⚠️ 평균 좋아요 비율이 0이거나 계산 불가능합니다.")
            return None

        return avg_like_ratio
    except Exception as e:
        print(f"파일 불러오기 실패: {e}")
        return None

# 개별 영상의 좋아요 비율 계산
def calculate_like_ratio(likes, views):
    try:
        if views == 0:
            return 0

        like_ratio = likes / views
        avg_like_ratio = get_average_like_ratio()

        if avg_like_ratio and avg_like_ratio != 0:
            diff_ratio = (like_ratio - avg_like_ratio) / avg_like_ratio * 100
            return diff_ratio
        else:
            return None
    except Exception as e:
        print(f"좋아요 비율 계산에 실패했습니다: {e}")
        return None
