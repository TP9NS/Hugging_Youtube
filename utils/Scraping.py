import requests
from bs4 import BeautifulSoup

def get_naver_news_by_keyword(keyword):
    url = f"https://search.naver.com/search.naver?ssc=tab.news.all&where=news&sm=tab_jum&query={keyword}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    news_list = []
    items = soup.select("a.news_tit")
    for item in items[:10]:
        title = item.get("title")
        link = item.get("href")
        news_list.append({"title": title, "url": link})
    return news_list

# 엔터 뉴스 크롤링
def get_naver_news_by_category(section_name):
    section_dict = {
        '정치': 100,
        '경제': 101,
        '사회': 102,
        '생활/문화': 103,
        '세계': 104,
        'IT/과학': 105
    }

    sid = section_dict[section_name]
    url = f"https://news.naver.com/section/{sid}"
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    }
    res = requests.get(url, headers=headers)
    news_list = []

    if res.ok:
        soup = BeautifulSoup(res.text, 'html.parser')
        a_tag_list = soup.select("div.sa_text a[href*='mnews/article']")

    for a_tag in a_tag_list:
        title = a_tag.get_text(strip=True)
        link = a_tag.get("href")

        if not title or not title.strip() or not link:
            continue

        if link.startswith("//"):
            link = "https:" + link

        news_list.append({"title": title, "url": link})

        if len(news_list) >= 10:
            break

    return news_list