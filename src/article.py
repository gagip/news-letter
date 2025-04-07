from dataclasses import dataclass
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup


@dataclass
class Article:
    title: str
    content: str
    url: str


def get_naver_news(query: str, num_articles: int) -> list[Article]:
    base_url = "https://search.naver.com/search.naver"
    params = {"where": "news", "query": query, "sort": "0"}  # 관련도순 정렬
    url = f"{base_url}?{urlencode(params)}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    for idx, news_area in enumerate(soup.select("div.news_area"), 1):
        title_element = news_area.select_one("a.news_tit")
        if title_element is None:
            continue
        article_url = title_element.get("href")
        if not isinstance(article_url, str):
            article_url = ""
        title = title_element.text.strip()
        content_element = news_area.select_one("div.news_dsc")
        if content_element is None:
            continue
        content = content_element.text.strip()
        content = content.replace("\n", " ").replace(
            "// flash 오류를 우회하기 위한 함수 추가function _flash_removeCallback() {}",
            "",
        )
        content = " ".join(content.split())
        articles.append(Article(title=title, content=content, url=article_url))
        if idx == num_articles:
            break
    return articles
