from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

# def get_related_videos(video_id: str, max_results: int = 5):
#     response = youtube.search().list(
#         part="snippet",  # ✅ 통계/statistics는 지원 안됨
#         relatedToVideoId=video_id,
#         type="video",  # ✅ 반드시 필요함
#         maxResults=max_results
#     ).execute()

#     results = []
#     for item in response.get("items", []):
#         video = {
#             "video_id": item["id"]["videoId"],
#             "title": item["snippet"]["title"],
#             "channel": item["snippet"]["channelTitle"],
#             "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
#             "description": item["snippet"]["description"]
#         }
#         results.append(video)
#     return results

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

def get_video_info(video_id: str):
    response = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()

    if response["items"]:
        item = response["items"][0]["snippet"]
        return {
            "title": item["title"],
            "channel": item["channelTitle"],
            "thumbnail": item["thumbnails"]["medium"]["url"]
        }
    else:
        return None
