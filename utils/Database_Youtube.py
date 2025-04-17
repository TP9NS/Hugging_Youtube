from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import requests
from collections import Counter

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_category_channel_recommendations(video_id, YOUTUBE_API_KEY, max_results=5):
    # Step 1: 영상의 categoryId와 channelId 가져오기
    info_url = "https://www.googleapis.com/youtube/v3/videos"
    info_params = {
        "part": "snippet",
        "id": video_id,
        "key": YOUTUBE_API_KEY
    }
    info_resp = requests.get(info_url, params=info_params).json()
    items = info_resp.get("items", [])
    if not items:
        print(f"❌ 영상 정보 조회 실패: {video_id}")
        return []

    snippet = items[0]["snippet"]
    category_id = snippet.get("categoryId")
    channel_id = snippet.get("channelId")

    print(f"🎯 categoryId: {category_id}, channelId: {channel_id}")

    # Step 2: 같은 채널 + 카테고리 기반 인기 영상 검색
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "type": "video",
        "videoCategoryId": category_id,
        "channelId": channel_id,
        "order": "viewCount",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY
    }

    search_resp = requests.get(search_url, params=search_params).json()

    results = []
    for item in search_resp.get("items", []):
        video = {
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
            "description": item["snippet"]["description"]
        }
        results.append(video)

    print(f"✅ 추천 영상 {len(results)}개 가져옴")
    return results

def get_videos_by_keyword(keyword: str, max_results: int = 5):
    response = youtube.search().list(
        part="snippet",
        q=keyword,
        type="video",
        order="viewCount",
        maxResults=max_results
    ).execute()

    results = []
    for item in response.get("items", []):
        video = {
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
            "description": item["snippet"]["description"]
        }
        results.append(video)
    return results

def get_video_info(video_id, YOUTUBE_API_KEY):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params).json()
    items = response.get("items", [])
    if not items:
        return None

    snippet = items[0]["snippet"]
    return {
        "title": snippet["title"],
        "channel": snippet["channelTitle"],
        "thumbnail": snippet["thumbnails"]["high"]["url"],
        "description": snippet.get("description", "")
    }

