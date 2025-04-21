from collections import Counter
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
from soynlp.noun import LRNounExtractor
import altair as alt
from matplotlib import rcParams

# 한글 폰트 설정
rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 불용어 제거 - 나중에 csv 파일로(stopwords.csv) 만들어서 불러오면 좋을 듯
STOPWORDS = {"좋아", "진짜", "좀", "약간", "되게", "정말", "그냥", "거", "때문", "것", "우리", "그것", "생각", "언니", "오빠", "형", "야", "있는"}

# 자막 텍스트에서 명사 추출 및 빈도수 계산 (soynlp 기반)
def extract_top_nouns(text: str, top_n: int = 10) -> Counter:
    texts = text.split('.')
    extractor = LRNounExtractor(verbose=False)
    noun_scores = extractor.train_extract(texts)
    sorted_nouns = sorted(noun_scores.items(), key=lambda x: x[1][0], reverse=True)
    top_nouns = Counter({noun: int(info[0]) for noun, info in sorted_nouns[:top_n*2] if noun not in STOPWORDS})
    filtered_nouns = dict(sorted(top_nouns.items(), key=lambda x: x[1], reverse=True)[:top_n])
    st.write("🔍 추출된 키워드 빈도:", filtered_nouns)
    return Counter(filtered_nouns)

# 파이 차트
def plot_pie_chart(freq_data: Counter, title: str = "상위 키워드 빈도수"):
    if not freq_data:
        st.warning("시각화할 데이터가 없습니다.")
        return
    labels, values = zip(*freq_data.items())
    colors = ['#daf8e3', '#97ebdb', '#00c2c7', '#0086ad', '#005582', '#b8e8ff', '#8ddfff', '#8cc2ff', '#7fa1ff', '#f0f9ff']
    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(
        values,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 10},
        colors=colors[:len(values)]
    )

    ax.legend(wedges, labels, title="키워드", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    ax.axis('equal')
    st.subheader("📊 주요 키워드 분포 (Pie Chart)")
    st.pyplot(fig)

# altair 바 (파이차트 우측)
def plot_bar_chart(freq_data: Counter, title: str = "상위 키워드 빈도수"):
    if not freq_data:
        st.warning("시각화할 데이터가 없습니다.")
        return
    df = pd.DataFrame(freq_data.items(), columns=["단어", "빈도"])
    st.write("📄 바 차트용 데이터프레임:", df)

    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("단어:N", sort="-y", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("빈도:Q"),
        tooltip=["단어", "빈도"]
    ).properties(title=title, width=600, height=400)

    st.subheader("📊 주요 키워드 분포 (Bar Chart)")
    st.altair_chart(chart, use_container_width=True)

# 통합 함수: 자막에서 키워드 추출 후 시각화
def visualize_keywords_from_text(text: str, chart_type: str = "pie"):
    freq_data = extract_top_nouns(text)
    if not freq_data:
        st.warning("키워드를 추출할 수 없습니다.")
        return

    if chart_type == "bar":
        plot_bar_chart(freq_data)
    else:
        plot_pie_chart(freq_data)