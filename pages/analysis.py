# pages/analysis.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
import matplotlib.font_manager as fm
import platform

from wordcloud import WordCloud
from konlpy.tag import Okt
from collections import Counter
from soynlp.noun import LRNounExtractor
import re
import matplotlib.pyplot as plt

# ✅ 한글 폰트 설정
def set_korean_font():
    if platform.system() == "Windows":
        plt.rc('font', family='Malgun Gothic')
    elif platform.system() == "Darwin":  # Mac
        plt.rc('font', family='AppleGothic')
    else:  # Linux
        font_dirs = ['/usr/share/fonts/truetype/nanum']
        font_files = fm.findSystemFonts(fontpaths=font_dirs)
        for font_file in font_files:
            fm.fontManager.addfont(font_file)
        plt.rc('font', family='NanumGothic')

    plt.rcParams['axes.unicode_minus'] = False

set_korean_font()

# ✅ API 로드
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=API_KEY)

# ✅ 인기 급상승 영상 50개 가져오기
def fetch_top50_videos():
    request = youtube.videos().list(
        part='snippet,statistics',
        chart='mostPopular',
        regionCode='KR',
        maxResults=50
    )
    response = request.execute()

    videos = []
    for item in response['items']:
        stats = item.get("statistics", {})
        videos.append({
            "title": item["snippet"]["title"],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0))
        })
    return pd.DataFrame(videos)

# ✅ Streamlit 앱
st.set_page_config(page_title="YouTube 영상 분석", page_icon="📊", layout="wide")
st.title("📊 인기 급상승 유튜브 영상 분석")
st.write("좋아요 수, 댓글 수, 조회수 간의 상관관계를 시각화합니다.")

# ✅ 데이터 로드
with st.spinner("데이터 불러오는 중..."):
    df = fetch_top50_videos()

st.dataframe(df)

# ✅ 상관관계 분석
st.subheader("🔗 상관관계 분석")
corr_col1, corr_col2 = st.columns(2)

with corr_col1:
    corr = df[["views", "likes", "comments"]].corr()
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="Blues", ax=ax)
    st.pyplot(fig)

with corr_col2:
    st.markdown("""
    #### 🔍 해석 가이드
    - **1.00**: 강한 양의 상관관계 (같이 증가)
    - **0.00**: 거의 관계 없음
    - **-1.00**: 강한 음의 상관관계 (반대로 움직임)
    ---
    - 예: 조회수와 좋아요가 0.9라면, 영상이 많이 보면 좋아요도 많이 누름
    - 예: 댓글 수는 참여도나 논란 정도를 보여줄 수 있음
    """)

# ✅ 산점도 시각화
st.subheader("📈 산점도 분석")
col1, col2 = st.columns(2)

with col1:
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    sns.scatterplot(data=df, x="views", y="likes", ax=ax1)
    ax1.set_title("조회수 vs 좋아요 수")
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    sns.scatterplot(data=df, x="views", y="comments", ax=ax2)
    ax2.set_title("조회수 vs 댓글 수")
    st.pyplot(fig2)

#워드 클라우드
st.subheader("📌 키워드 분석")

# 명사 추출 함수 (빈도를 세도록 수정)
def extract_nouns(texts):
    okt = Okt()
    noun_extractor = LRNounExtractor(verbose=False)
    soy_nouns_dict = noun_extractor.train_extract(texts)
    soy_nouns = set(word for word, score in soy_nouns_dict.items() if score >= 0.5)

    compound_nouns = ['브이로그', '엔시티', '네이버', '유튜브', '남편']  # 복합어 예시

    all_nouns = []

    for text in texts:
        okt_noun_list = okt.nouns(text)
        okt_noun_list = [combine_compound_nouns(word, compound_nouns) for word in okt_noun_list]

        # SoyNLP 명사도 포함
        soy_in_text = [word for word in soy_nouns if word in text]
        all_nouns.extend(okt_noun_list + soy_in_text)

    return all_nouns

# 복합어 합치기
def combine_compound_nouns(word, compound_nouns):
    for compound in compound_nouns:
        if compound in word or word in compound:
            return compound
    return word

# 텍스트에서 불용어 및 특수 문자 제거
def preprocess_text(text):
    # 한글 및 공백만 남기고 모두 제거
    text = re.sub(r"[^\w\sㄱ-ㅎ가-힣]", "", text)
    #text = re.sub(r"\s+", " ", text)  # 여러 공백을 하나로
    return text.strip()

# 예시 텍스트들을 유튜브 영상 제목에서 가져오기
texts = df['title'].tolist()  # 데이터프레임에서 'title' 컬럼을 가져와 리스트로 변환

# 텍스트 전처리
texts = [preprocess_text(text) for text in texts]

# 명사 추출
nouns = extract_nouns(texts)

# 명사 빈도 계산
nouns_counter = Counter(nouns)

# 상위 50개 명사
top_nouns = dict(nouns_counter.most_common(50))

# 워드 클라우드 생성
wordcloud = WordCloud(
    font_path="malgun.ttf" if platform.system() == "Windows" else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    background_color="white",
    width=800,
    height=600
).generate_from_frequencies(top_nouns)

# 워드 클라우드 시각화
plt.figure(figsize=(10, 6))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
st.pyplot(plt)
plt.close() 

# 상위 50개 명사 표시
st.write("상위 50개 명사:", top_nouns)
st.success("✅ 분석 완료!")