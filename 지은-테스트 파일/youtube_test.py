from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable
from transformers import pipeline, AutoTokenizer
from typing import List
import re
import urllib.parse

#YouTube URL에서 v 파라미터를 추출하여 영상 ID를 반환
def extract_video_id_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    return query.get("v", [None])[0]

#영상 ID를 이용해 한국어 자막을 불러오고, 
#자막 텍스트들을 하나의 문자열로 합침.
def fetch_youtube_transcript(video_url: str) -> str:
    video_id = extract_video_id_from_url(video_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL.")

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        transcript = " ".join([item['text'] for item in transcript_list])
        return transcript
    except TranscriptsDisabled:
        raise ValueError("Transcripts are disabled for this video.")
    except VideoUnavailable:
        raise ValueError("Video is unavailable.")
    except Exception as e:
        raise ValueError(f"Unexpected error occurred: {str(e)}")

#자막 텍스트를 전처리
def preprocess_transcript(text: str) -> str:
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'(?<=[가-힣])(?=[A-Z])', '. ', text)
    text = re.sub(r'\.(?=[가-힣])', '. ', text)
    return text.strip()

#전체 자막 텍스트를 문장 단위로 쪼개어,
#모델의 토큰 수 제한에 맞게 나눔.
def chunk_text_by_sentence(text: str, tokenizer, max_tokens: int = 512, min_tokens: int = 50) -> List[str]:
    sentences = re.split(r'(?<=[.!?다요임])(?=\s)', text)
    chunks, current_chunk = [], []

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        current_chunk.append(sent)
        joined = " ".join(current_chunk)
        input_len = len(tokenizer(joined)["input_ids"])

        if input_len >= max_tokens:
            chunk = " ".join(current_chunk[:-1]).strip()
            if len(tokenizer(chunk)["input_ids"]) >= min_tokens:
                chunks.append(chunk)
            current_chunk = [sent]

    if current_chunk:
        final_chunk = " ".join(current_chunk).strip()
        if len(tokenizer(final_chunk)["input_ids"]) >= min_tokens:
            chunks.append(final_chunk)

    return chunks

#모델이 생성한 요약 결과를 문장 단위로 분리하고 문장 부호를 보정
def postprocess_summary(text: str) -> str:
    sentences = re.split(r'(?<=[다|요|죠|임])(?=[\s\n])', text)
    return " ".join(s.strip() + "." if not s.endswith(".") else s for s in sentences if s.strip())

#최종 요약 결과에서 최대 문장 수만 남기고 잘라냄.
def limit_summary_sentences(summary: str, max_sentences: int = 5) -> str:
    sentences = re.split(r'(?<=[.?!다요죠임])\s+', summary)
    trimmed = sentences[:max_sentences]
    return " ".join(s.strip().rstrip('.') + '.' for s in trimmed if s.strip())

#전체 자막 텍스트를 
#전처리 → 분할 → 요약 → 후처리 → 문장 수 제한 과정을 거쳐 
#최종 요약문을 반환
def summarize_transcript(
    text: str,
    model_name: str = "lcw99/t5-base-korean-text-summary",
    summary_strength: str = "중간"
) -> str:
    text = preprocess_transcript(text)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    summarizer = pipeline("summarization", model=model_name, tokenizer=tokenizer)

    # 💡 요약 강도에 따라 매개변수 다르게 설정
    if summary_strength == "짧게":
        min_len, max_len = 30, 60
        max_sentences = 3
        chunk_limit = 1
        ratio = 0.3
    elif summary_strength == "길게":
        min_len, max_len = 100, 200
        max_sentences = 8
        chunk_limit = None  # 전체
        ratio = 0.8
    else:  # 중간
        min_len, max_len = 50, 120
        max_sentences = 5
        chunk_limit = 2
        ratio = 0.5

    chunks = chunk_text_by_sentence(text, tokenizer)
    if chunk_limit is not None:
        chunks = chunks[:chunk_limit]

    print(f"[INFO] 요약 강도: {summary_strength}, 사용 chunk 수: {len(chunks)}")
    summaries = []

    for idx, chunk in enumerate(chunks):
        input_len = len(tokenizer(chunk)["input_ids"])
        dynamic_max_len = int(input_len * ratio)
        dynamic_max_len = min(max(dynamic_max_len, min_len), max_len)

        print(f"  [Chunk {idx+1}] input_len: {input_len}, max_len: {dynamic_max_len}")
        result = summarizer(
            chunk,
            max_length=dynamic_max_len,
            min_length=min_len,
            do_sample=False
        )[0]['summary_text']
        print(f"    요약 결과: {result[:50]}...")
        summaries.append(result)

    cleaned_summary = postprocess_summary(" ".join(summaries))
    limited_summary = limit_summary_sentences(cleaned_summary, max_sentences=max_sentences)

    print(f"[INFO] 최종 문장 수: {len(re.split(r'(?<=[다요죠임])[\\s\\n]+', limited_summary))}")
    return limited_summary


if __name__ == "__main__":
    test_video_url = 'https://www.youtube.com/watch?v=MHyaDHWkA2Y'
    try:
        transcript = fetch_youtube_transcript(test_video_url)
        print("Original Transcript Preview:")
        print(transcript[:500], "...\n")

        summary = summarize_transcript(transcript, summary_strength="길게")
        print("\nSummarized Transcript:")
        print(summary)

    except ValueError as e:
        print("Error:", e)