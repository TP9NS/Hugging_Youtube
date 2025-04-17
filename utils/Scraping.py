import requests
from bs4 import BeautifulSoup

# Selenium WebDriver 설정
def get_naver_news_by_keyword(keyword):
    url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    news_items = soup.select("ul.list_news div.news_wrap.api_ani_send")
    news_list = []

    for item in news_items:
        title_tag = item.select_one("a.news_tit")
        img_tag = item.select_one("img")

        title = title_tag.get("title") if title_tag else "제목 없음"
        link = title_tag.get("href") if title_tag else "#"

        # ✅ 썸네일: data-src → src → 기본 썸네일
        thumbnail = None
        if img_tag:
            thumbnail = img_tag.get("data-src") or img_tag.get("src")
        if not thumbnail:
            thumbnail = "https://example.com/default_thumbnail.jpg"

        news_list.append({
            "title": title,
            "url": link,
            "thumbnail": thumbnail
        })

        if len(news_list) >= 10:
            break

    return news_list
    options = Options()
    options.headless = True  # 브라우저 UI 없이 백그라운드에서 실행
    driver = webdriver.Chrome(executable_path="path/to/chromedriver", options=options)
    
    url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
    driver.get(url)  # 페이지 로드
    html = driver.page_source  # 페이지 소스 가져오기
    
    # 예: get_naver_news_by_category 안에서
    res = requests.get(url, headers=headers)
    
    soup = BeautifulSoup(html, "html.parser")
    news_items = soup.select("ul.list_news div.news_wrap.api_ani_send")
    
    news_list = []
    
    for item in news_items:
        title_tag = item.select_one("a.news_tit")
        
        # 썸네일 이미지 찾기
        img_tag = item.select_one("img#img1") or item.select_one("img._LAZY_LOADING")
        
        title = title_tag.get("title") if title_tag else "제목 없음"
        link = title_tag.get("href") if title_tag else "#"
        
        # img_tag에서 data-src 속성을 사용해 썸네일 가져오기
        thumbnail = img_tag.get("data-src") if img_tag and img_tag.has_attr('data-src') else img_tag.get("src") if img_tag else "https://example.com/default_thumbnail.jpg"
        
        if thumbnail.startswith("//"):  # 상대경로일 경우 절대경로로 변환
            thumbnail = "https:" + thumbnail
        
        news_list.append({
            "title": title,
            "url": link,
            "thumbnail": thumbnail
        })
        
        if len(news_list) >= 10:
            break
    
    driver.quit()  # WebDriver 종료
    
    return news_list

# 📂 카테고리 기반 뉴스 크롤링 (썸네일 포함)
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