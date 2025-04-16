import os
import requests
from googleapiclient.discovery import build
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from dotenv import load_dotenv
# 한국어 감정 분석기 초기화
MODEL_NAME = "monologg/koelectra-small-finetuned-nsmc"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
sentiment_model = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

def get_video_id_from_url(url: str) -> str:
    """유튜브 URL에서 video_id 추출"""
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    else:
        raise ValueError("유효하지 않은 YouTube URL입니다.")

def get_youtube_comments(api_key: str, video_id: str, max_results: int = 50) -> list:
    """YouTube Data API를 사용하여 댓글 가져오기"""
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        textFormat="plainText"
    )
    response = request.execute()
    
    comments = []
    for item in response.get("items", []):
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comments.append(comment)
        
    for i, c in enumerate(comments[:10]):
        print(f"{i+1}. {c}")
    return comments

def analyze_sentiments(comments: list) -> dict:
    """댓글 리스트를 받아 감정 분석 결과 요약"""
    results = sentiment_model(comments)
    summary = {}

    for res in results:
        label = res["label"]
        summary[label] = summary.get(label, 0) + 1

    total = sum(summary.values())
    summary_percent = {
        label: f"{(count / total * 100):.1f}%" for label, count in summary.items()
    }
    return summary_percent

def process_youtube_url(url: str, api_key: str, max_comments: int = 50) -> dict:
    """URL을 입력받아 댓글 감정 분석 결과 반환"""
    video_id = get_video_id_from_url(url)
    comments = get_youtube_comments(api_key, video_id, max_comments)
    if not comments:
        return {"error": "댓글이 없습니다."}
    return analyze_sentiments(comments)