from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import requests
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

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

def get_top_recommendations_from_watch_history(watch_history, YOUTUBE_API_KEY, max_results=5):
    all_recommended = []

    for record in watch_history:
        video_id = record["video_id"]
        try:
            related = get_category_channel_recommendations(video_id, YOUTUBE_API_KEY, max_results=max_results)
            for video in related:
                all_recommended.append(video["video_id"])
        except Exception as e:
            print(f"⚠ 추천 실패 (video_id: {video_id}): {e}")
            continue

    counter = Counter(all_recommended)
    top_video_ids = [vid for vid, _ in counter.most_common(3)]

    # video_id만 있는 상태이므로, 다시 영상 정보 요청
    top_videos = []
    for video_id in top_video_ids:
        info = get_video_info(video_id, YOUTUBE_API_KEY)
        if info:
            top_videos.append({
                "video_id": video_id,
                "title": info["title"],
                "channel": info["channel"],
                "thumbnail": info["thumbnail"],
                "description": info.get("description", "")
            })

    return top_videos


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

def analyze_watch_history_similarity(watch_history, api_key):
    # 1. 시청 기록에서 title + description 수집
    documents = []
    video_ids = []
    for record in watch_history:
        video_id = record["video_id"]
        info = get_video_info(video_id, api_key)
        if info:
            text = f"{info['title']} {info.get('description', '')}"
            documents.append(text)
            video_ids.append(video_id)

    if len(documents) < 2:
        print("⚠️ 분석할 영상이 2개 이상 필요합니다.")
        return []

    # 2. TF-IDF 벡터화
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)

    # 3. 코사인 유사도 계산
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # 4. 상위 유사도 영상쌍 추출
    pairs = []
    for i in range(len(video_ids)):
        for j in range(i + 1, len(video_ids)):
            score = similarity_matrix[i][j]
            pairs.append((video_ids[i], video_ids[j], round(score, 3)))

    # 유사도 높은 순으로 정렬
    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs
