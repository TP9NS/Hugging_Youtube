import firebase_admin
from firebase_admin import credentials, db
import os

# Firebase 초기화 (앱 중복 초기화 방지)
if not firebase_admin._apps:
    cred = credentials.Certificate("hugging-75b21-firebase-adminsdk-fbsvc-2d15d78844.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://hugging-75b21-default-rtdb.firebaseio.com/'
    })

# 검색어 저장
def save_search(user_id: str, keyword: str):
    ref = db.reference(f'users/{user_id}/search_history')
    ref.push({
        'keyword': keyword
    })

# 시청기록 저장
def save_watch_history(user_id: str, video_id: str):
    ref = db.reference(f'users/{user_id}/watch_history')
    ref.push({
        'video_id': video_id
    })
# 정보 불러오기
def get_history(user_id, category):
    ref = db.reference(f"users/{user_id}/{category}")
    data = ref.get()
    if data:
        return [item for item in data.values()]
    return []