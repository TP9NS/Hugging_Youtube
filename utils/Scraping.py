from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_naver_news_by_keyword(keyword):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(options=options)
    url = f"https://search.naver.com/search.naver?where=news&query={keyword}"

    try:
        driver.get(url)

        # 뉴스 영역 전체 로드될 때까지 기다림
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href^='https://']"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # class명이 난수라서 a태그에서 href만 걸러냄
        news_blocks = soup.select("div.sds-comps-vertical-layout.sds-comps-full-layout.Ermefm6A3ilpd9Zvt0OZ")
        
        news_list = []
        for block in news_blocks[:10]:  # 최대 10개 블록만 처리
            # 1. 기사 링크와 제목 추출 (클래스명이 동적이므로 부분 일치 사용)
            title_link = block.select_one('a[class*="jT1DuARpwIlNAFMacxlu"]')
            if not title_link:
                continue  # 필수 요소가 없으면 건너뜀
                
            title = title_link.get_text(strip=True)
            url = title_link['href']

            # 2. 이미지 URL 추출
            img_tags = block.select('img[src*="search.pstatic.net"]')
            if len(img_tags) > 1:
                img_url = img_tags[1]['src']
            elif len(img_tags) > 0:
                img_url = img_tags[0]['src']
            else:
                img_url = "https://example.com/default_thumbnail.jpg"  # 기본 이미지
            
            news_list.append({
                "title": title,
                "url": url,
                "thumbnail": img_url
            })

        return news_list

    finally:
        driver.quit()

# 📂 카테고리 기반 뉴스 크롤링 (썸네일 포함)
def get_naver_news_by_category(section_name):
    section_dict = {
        '정치': 100,
        '경제': 101,
        '사회': 102,
        '생활/문화': 103,
        '세계': 104,
        'IT/과학': 105
    }

    sid = section_dict.get(section_name)
    if sid is None:
        return []

    url = f"https://news.naver.com/section/{sid}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    }

    res = requests.get(url, headers=headers)
    news_list = []

    if res.ok:
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select("ul.sa_list > li")

        for item in items:
            a_tag = item.select_one("div.sa_text a")
            img_tag = item.select_one("img")

            title = a_tag.get_text(strip=True) if a_tag else None
            link = a_tag['href'] if a_tag and a_tag.has_attr('href') else None

            # ✅ 썸네일: data-src → src → 기본 썸네일
            thumbnail = None
            if img_tag:
                thumbnail = img_tag.get("data-src") or img_tag.get("src")
            if not thumbnail:
                thumbnail = "https://example.com/default_thumbnail.jpg"

            if not title or not link:
                continue

            if link.startswith("//"):
                link = "https:" + link

            news_list.append({
                "title": title,
                "url": link,
                "thumbnail": thumbnail
            })

            if len(news_list) >= 10:
                break

    return news_list