from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import requests
from collections import Counter
import json

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def get_video_info(video_id, YOUTUBE_API_KEY):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "id": video_id,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params).json()
    print("요청 ID:", video_id)
    print("응답:", json.dumps(response, indent=2, ensure_ascii=False))

    items = response.get("items", [])
    if not items:
        return None

    snippet = items[0]["snippet"]
    stats = items[0].get("statistics", {})

    return {
        "title": snippet["title"],
        "channel": snippet["channelTitle"],
        "channel_id": snippet["channelId"],
        "thumbnail": snippet["thumbnails"]["high"]["url"],
        "description": snippet.get("description", ""),
        "video_id": video_id
    }

def get_videos_by_keyword(keyword: str, YOUTUBE_API_KEY, max_results: int = 5):
    response = youtube.search().list(
        part="snippet",
        q=keyword,
        type="video",
        maxResults=max_results
    ).execute()

    results = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        detailed = get_video_info(video_id, YOUTUBE_API_KEY)
        if detailed:
            results.append(detailed)
    return results

def get_category_channel_recommendations(video_id, YOUTUBE_API_KEY, max_results=5): 
    def fetch_video_info(video_id):
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet",
            "id": video_id,
            "key": YOUTUBE_API_KEY
        }
        resp = requests.get(url, params=params).json()
        items = resp.get("items", [])
        if not items:
            return None
        snippet = items[0]["snippet"]
        return {
            "channel_id": snippet.get("channelId"),
            "category_id": snippet.get("categoryId")
        }

    def search_videos(channel_id, category_id=None):
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "order": "viewCount",
            "type": "video",
            "maxResults": max_results + 1,
            "key": YOUTUBE_API_KEY
        }
        if category_id:
            params["videoCategoryId"] = category_id

        resp = requests.get(url, params=params).json()
        return resp.get("items", [])

    info = fetch_video_info(video_id)
    if not info:
        print(f"❌ 영상 정보 조회 실패: {video_id}")
        return []

    print(f"channelId: {info['channel_id']}, categoryId: {info['category_id']}")
    items = search_videos(info["channel_id"], info["category_id"])

    if not items:
        print("⚠️ 관련 카테고리 영상 없음 → 채널만 기준으로 재검색")
        items = search_videos(info["channel_id"])

    results = []
    for item in items:
        vid = item["id"]["videoId"]
        if vid == video_id:
            continue

        detailed = get_video_info(vid, YOUTUBE_API_KEY)
        if detailed:
            results.append(detailed)

        if len(results) >= max_results:
            break

    print(f"✅ 추천 영상 {len(results)}개 가져옴")
    return results