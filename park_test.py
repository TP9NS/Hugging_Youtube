import os
from CommentsAnalysis import process_youtube_url
from CommentsGenAI import process_youtube_comments
from dotenv import load_dotenv
load_dotenv() # env 파일 초기화
 
video_url = "https://www.youtube.com/watch?v=MHyaDHWkA2Y"
API_KEY = os.getenv("GOOGLE_API_KEY")
result = process_youtube_url(video_url, API_KEY)
#process_youtube(api key ,url, 댓글 수 defalut = 30 )
result2 = process_youtube_comments(API_KEY,video_url)
print(result)

print(result2)