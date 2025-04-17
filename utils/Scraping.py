from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import requests
def test_naver_html(keyword):
    url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    res = requests.get(url, headers=headers)
    print("status:", res.status_code)
    print("length:", len(res.text))
    print(res.text)
    with open("naver_debug.html", "w", encoding="utf-8") as f:
        f.write(res.text)


def get_naver_news_by_keyword(keyword):
    options = Options()
    options.add_argument("--headless")  # 창 안 띄우기
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
    driver.get(url)
    time.sleep(2)  # 페이지 로딩 기다리기

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    news_list = []

    items = soup.select("ul.list_news > li.bx")

    for item in items:
        title_tag = item.select_one("a.news_tit")
        img_tag = item.select_one("a.dsc_thumb img")

        title = title_tag.get("title") if title_tag else None
        link = title_tag.get("href") if title_tag else None
        thumbnail = img_tag.get("data-src") or img_tag.get("src") if img_tag else "https://via.placeholder.com/120x80"

        if not title or not link:
            continue

        news_list.append({
            "title": title,
            "url": link,
            "thumbnail": thumbnail
        })

        if len(news_list) >= 10:
            break

    return news_list



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