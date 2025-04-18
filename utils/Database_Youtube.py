from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import requests
from collections import Counter

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

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

    # Step 1: 영상의 채널/카테고리 정보 가져오기
    info = fetch_video_info(video_id)
    if not info:
        print(f"❌ 영상 정보 조회 실패: {video_id}")
        return []

    print(f"🎯 channelId: {info['channel_id']}, categoryId: {info['category_id']}")

    # Step 2: 채널 + 카테고리 기반 검색
    items = search_videos(info["channel_id"], info["category_id"])

    # Step 3: fallback (카테고리 없이 채널 기준만으로)
    if not items:
        print("⚠️ 관련 카테고리 영상 없음 → 채널만 기준으로 재검색")
        items = search_videos(info["channel_id"])

    # Step 4: 결과 정리
    results = []
    for item in items:
        vid = item["id"]["videoId"]
        if vid == video_id:
            continue  # 자기 자신 제외
        snippet = item["snippet"]
        results.append({
            "video_id": vid,
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "thumbnail": snippet["thumbnails"]["high"]["url"],
            "description": snippet.get("description", "")
        })
        if len(results) >= max_results:
            break

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
        "channel_id": snippet["channelId"],
        "thumbnail": snippet["thumbnails"]["high"]["url"],
        "description": snippet.get("description", "")
    }

