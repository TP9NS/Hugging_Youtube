import os
from utils.TranscriptSummarize import fetch_youtube_transcript, summarize_transcript
from dotenv import load_dotenv
load_dotenv() # env 파일 초기화
 
video_url = "https://www.youtube.com/watch?v=MHyaDHWkA2Y"
API_KEY = os.getenv("GOOGLE_API_KEY")

transcript = fetch_youtube_transcript(video_url)
summary = summarize_transcript(transcript, summary_strength="길게")

print("=== 요약 결과 ===")
print(summary)

# <요약 과정>
# 1. 영상의 자막 추출
# fetch_youtube_transcript(video_url)

# 2. 자막 텍스트를 전처리(공백 제거, 잘못된 구두점/형식 정리)
# preprocess_transcript

# 3. 자막을 chunk 단위로 나눔(너무 길면 모델이 처리 못하기 때문에 
# 적절한 길이(토큰 기준)로 분할)
# 기준: 문장 단위로 분리 + tokenizer 길이 고려
# chunk_text_by_sentence

# 4. 각 chunk에 대해 Huggingface 모델로 요약 수행
# chunk마다 요약 수행 후 → 결과 모음
# summarizer(chunk, max_length=..., min_length=...)

# 5. 요약된 결과들을 하나로 합쳐서 후처리
# postprocess_summary(...)
# 마침표 붙이기 등 정리
# limit_summary_sentences(...)
# 요약 강도별 문장 수 제한

#<전체 과정 요약>
# video_url → transcript → chunk 나누기 → 각 chunk 요약 → 문장 정리 
# → 원하는 줄 수로 자르기 → 최종 요약 출력