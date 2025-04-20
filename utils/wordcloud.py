from konlpy.tag import Okt
from soynlp.noun import LRNounExtractor
import re
from collections import Counter

# ✅ 복합어 합치기 함수, 예: '브이' 또는 '로그' → '브이로그'
def combine_compound_nouns(word, compound_nouns):
    for compound in compound_nouns:
        if compound in word or word in compound:
            return compound
    return word

# ✅ 텍스트 전처리 함수, 한글과 공백만 남기고 나머지 문자(이모지, 특수문자 등)는 제거
def preprocess_text(text):
    text = re.sub(r"[^\w\sㄱ-ㅎ가-힣]", "", text)
    return text.strip()

# ✅ 명사 추출 함수 (Okt + SoyNLP 혼합)
def extract_nouns(texts, compound_nouns=None):
    if compound_nouns is None:
        compound_nouns = ['브이로그', '엔시티', '네이버', '유튜브', '남편']  # 기본 복합어 리스트

    okt = Okt()

    # ✅ soynlp 학습 기반 명사 추출 (LRNounExtractor는 전체 텍스트 학습 필요)
    noun_extractor = LRNounExtractor(verbose=False)
    soy_nouns_dict = noun_extractor.train_extract(texts)
    soy_nouns = set(word for word, score in soy_nouns_dict.items() if score >= 0.5)

    total_nouns = Counter()

    for text in texts:
        # ✅ Okt 명사 추출
        okt_nouns = okt.nouns(text)
        # ✅ 복합어 통합
        okt_nouns = [combine_compound_nouns(word, compound_nouns) for word in okt_nouns]
        # ✅ 해당 텍스트에 포함된 soynlp 명사 추출
        soy_in_text = [word for word in soy_nouns if word in text]
        # ✅ 한글자 단어 제거 + 중복 제거
        unique_nouns = set(okt_nouns + soy_in_text)
        filtered_nouns = {word for word in unique_nouns if len(word) >= 2}
        total_nouns.update(filtered_nouns)

    return total_nouns
