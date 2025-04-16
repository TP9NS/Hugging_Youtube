import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
import openai
import re
# Load environment variables
load_dotenv()

# 최신 버전 OpenAI 클라이언트 객체 생성
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_video_id(url: str) -> str:
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    raise ValueError("유효하지 않은 유튜브 링크입니다.")

def fetch_youtube_comments(api_key: str, video_id: str, max_results: int = 30) -> list:
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.commentThreads().list(
        part="snippet", videoId=video_id, maxResults=max_results, textFormat="plainText"
    )
    response = request.execute()
    comments = [
        item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        for item in response.get("items", [])
    ]
    return comments

def analyze_with_gpt(comments: list) -> str:
    numbered_comments = "\n".join([f"{i+1}. {c}" for i, c in enumerate(comments)])
    prompt = f"""
다음은 유튜브 영상에 달린 댓글들입니다. 각 댓글의 감정을 고려하여 전체적인 감정 비율을 분석해주세요.
감정 비율은 '긍정', '부정', '모르겠음'의 세 가지로 구분합니다.

또한, 댓글들의 주요 내용을 요약해 주세요.

댓글:
{numbered_comments}

응답 형식:
감정 비율:
- 긍정: ??%
- 부정: ??%
- 모르겠음: ??%

요약:
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content

#gpt 응답 parsing
def parse_gpt_response(response_text: str) -> dict:
    sentiment_lines = re.findall(r'- (\S+): (\d+%)', response_text)
    sentiment_dict = {label: percent for label, percent in sentiment_lines}

    summary_match = re.search(r'요약:\s*(.+)', response_text, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""

    return {
        "sentiment_summary": sentiment_dict,
        "summary": summary
    }

#호출 함수
def process_youtube_comments(api_key: str, url: str, num_comments: int = 30) -> str:
    video_id = get_video_id(url)
    comments = fetch_youtube_comments(api_key, video_id, num_comments)
    if not comments:
        return "댓글을 불러오지 못했습니다."
    gpt_dict = analyze_with_gpt(comments)
    return parse_gpt_response(gpt_dict)
