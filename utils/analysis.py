# utils/comment_analysis.py
import pandas as pd

def analyze_comments(video_id):
    # 실제로는 API 또는 크롤링 + 감정 분석
    return pd.DataFrame({
        'sentiment': ['positive', 'negative', 'neutral'],
        'count': [120, 30, 50]
    })
