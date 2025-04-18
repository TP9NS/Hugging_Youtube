from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_recommendations_by_category_name(category_name, YOUTUBE_API_KEY, max_results=5):
    """
    카테고리 이름을 검색어로 사용해서 추천 영상 목록을 반환
    ex: "Pets & Animals" → "Pets & Animals 하이라이트" 검색
    """
    from utils.Database_Youtube import get_videos_by_keyword  # 또는 현재 정의 위치에 따라 import 생략

    query = f"{category_name} 하이라이트"  # 또는 단순히 category_name만 써도 됨
    return get_videos_by_keyword(query, YOUTUBE_API_KEY, max_results=max_results)
