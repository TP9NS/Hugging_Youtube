import os
from utils.CommentsAnalysis import process_youtube_url
from utils.CommentsGenAI import process_youtube_comments
from utils.TranscriptSummarize import summarize_transcript,fetch_youtube_transcript
from dotenv import load_dotenv
load_dotenv() # env 파일 초기화
 
video_url = "https://www.youtube.com/watch?v=MHyaDHWkA2Y"
API_KEY = os.getenv("GOOGLE_API_KEY")
#result = process_youtube_url(video_url, API_KEY)

#process_youtube_comments(api key ,url, 댓글 수 defalut = 30 )
result2 = process_youtube_comments(API_KEY,video_url) # dict 형식으로 반환 -> 'sentiment_summary': {'긍정': '40%', '부정': '50%', '모르겠음': '10%'}, 'summary': '어쩌구저쩌구'
#summarize_transscript(str(script) , [짧게, 중간 , 길게])
result3 = summarize_transcript(fetch_youtube_transcript(video_url), summary_strength="길게") # str 형식으로 요약 정보 반환 
#print(result)
print(result2)

#print(result3)