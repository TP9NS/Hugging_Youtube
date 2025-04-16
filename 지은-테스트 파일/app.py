# app.py
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable
from transformers import pipeline, AutoTokenizer
from typing import List
import re
import urllib.parse

def extract_video_id_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    return query.get("v", [None])[0]

def fetch_youtube_transcript(video_url: str) -> str:
    video_id = extract_video_id_from_url(video_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL.")
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        return " ".join([item['text'] for item in transcript_list])
    except TranscriptsDisabled:
        raise ValueError("자막이 비활성화된 영상입니다.")
    except VideoUnavailable:
        raise ValueError("영상이 존재하지 않거나 접근할 수 없습니다.")
    except Exception as e:
        raise ValueError(f"예기치 못한 오류: {str(e)}")

def preprocess_transcript(text: str) -> str:
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'(?<=[가-힣])(?=[A-Z])', '. ', text)
    text = re.sub(r'\.(?=[가-힣])', '. ', text)
    return text.strip()

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

def postprocess_summary(text: str) -> str:
    sentences = re.split(r'(?<=[다|요|죠|임])(?=[\s\n])', text)
    return " ".join(s.strip() + "." if not s.endswith(".") else s for s in sentences if s.strip())

def limit_summary_sentences(summary: str, max_sentences: int = 5) -> str:
    sentences = re.split(r'(?<=[.?!다요죠임])\s+', summary)
    trimmed = sentences[:max_sentences]
    return " ".join(s.strip().rstrip('.') + '.' for s in trimmed if s.strip())

def summarize_transcript(text: str, model_name: str, summary_strength: str) -> str:
    text = preprocess_transcript(text)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    summarizer = pipeline("summarization", model=model_name, tokenizer=tokenizer)
    if summary_strength == "짧게":
        min_len, max_len, max_sentences = 20, 60, 3
    elif summary_strength == "길게":
        min_len, max_len, max_sentences = 100, 200, 8
    else:
        min_len, max_len, max_sentences = 50, 120, 5
    chunks = chunk_text_by_sentence(text, tokenizer)
    summaries = []
    for chunk in chunks:
        input_len = len(tokenizer(chunk)["input_ids"])
        dynamic_max_len = min(max(input_len // 2, min_len), max_len)
        result = summarizer(chunk, max_length=dynamic_max_len, min_length=min_len, do_sample=False)[0]['summary_text']
        summaries.append(result)
    cleaned = postprocess_summary(" ".join(summaries))
    return limit_summary_sentences(cleaned, max_sentences)

# ─── Streamlit App ───────────────────────────────────────────────
st.set_page_config(page_title="Korean YouTube 요약기", layout="centered")

st.title("🎬 YouTube 자막 요약기 (한국어)")
video_url = st.text_input("유튜브 영상 URL을 입력하세요:")
summary_strength = st.selectbox("요약 강도 선택:", ["짧게", "보통", "길게"])
run_button = st.button("요약하기")

if run_button:
    if not video_url.strip():
        st.warning("유튜브 URL을 입력해주세요.")
    else:
        try:
            with st.spinner("자막 불러오는 중..."):
                transcript = fetch_youtube_transcript(video_url)
            st.success("자막 불러오기 성공 ✅")
            st.markdown("**자막 미리보기:**")
            st.text(transcript[:500] + "...")
            with st.spinner("요약 중..."):
                summary = summarize_transcript(
                    transcript,
                    model_name="lcw99/t5-base-korean-text-summary",
                    summary_strength=summary_strength
                )
            st.success("요약 완료 🎉")
            st.markdown("### 📝 요약 결과")
            st.markdown(summary)
        except ValueError as e:
            st.error(str(e))
