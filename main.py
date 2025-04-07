import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import anthropic
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import os

from src.llm_provider import ClaudeProvider, LLMProvider

client: LLMProvider = ClaudeProvider(api_key="") 

smtp_password = "password here"  # 실제 비밀번호로 대체


def get_naver_news(query: str, num_articles: int):
    base_url = "https://search.naver.com/search.naver"
    params = {
        "where": "news",
        "query": query,
        "sort": "0"  # 관련도순 정렬
    }
    url = f"{base_url}?{urlencode(params)}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    for idx, news_area in enumerate(soup.select("div.news_area"), 1):
        title_element = news_area.select_one("a.news_tit")
        if title_element is None:
            continue
        article_url = title_element.get("href")
        title = title_element.text.strip()
        content_element = news_area.select_one("div.news_dsc")
        if content_element is None:
            continue
        content = content_element.text.strip()
        content = content.replace("\n", " ").replace("// flash 오류를 우회하기 위한 함수 추가function _flash_removeCallback() {}", "")
        content = ' '.join(content.split())
        articles.append({
            "title": title,
            "content": content,
            "url": article_url
        })
        if idx == num_articles:
            break
    return articles

def summarize_articles(articles: list):
    summaries = []
    for article in articles:
        prompt = f"""
        다음 기사를 200자 내외로 인사와 '기사를 요약하겠다'는 내용은 제외하고 친절한 말투로 요약해주세요:
        제목: {article['title']}
        본문: {article['content']}
        """
        summary = client.create(prompt)
        summaries.append(summary)
    return summaries

def generate_newsletter(query, articles, summaries):
    today = datetime.now().strftime("%m월 %d일")
    content = ""

    for article, summary in zip(articles, summaries):
        content += f"""
        <div style="max-width:90%;margin-left:auto;margin-right:auto;margin-top:40px" class="nomal-paragraph">
          <div style="font-weight:bold;font-size:18px;margin-bottom:10px">{article['title']}</div>
          <div style="margin-top:20px">{summary}</div>
          <div style="margin-top:10px"><a href="{article['url']}" target="_blank">{article['url']}</a></div>
        </div>
        """
    # 요약된 본문 전체를 다시 하나로 묶어서 브리핑하는 문단 생성
    prompt = f"""
    다음 기사 요약들을 하나로 묶어서 전체 뉴스레터에 대해 브리핑하는 문단을 300자 내외로 생성해주세요:

    기사 요약:
    {summaries}
    """
    briefing = client.create(prompt)

    newsletter = f"""
    <div style="width:100%">
      <div style="max-width:600px;margin:0 auto;padding:60px 0 30px 0;font-family:'Roboto',Arial,Helvetica,sans-serif;font-size:16px;line-height:1.5;border:1px solid #e2e2e2">
        <div align="center" style="padding-right:0px;padding-left:0px;background-color:#000000;padding:20px 0" class="logo-area">
          <h1 style="color:#ffffff;font-size:48px;margin:0">DECK</h1>
          <h2 style="color:#ffffff;font-size:24px;margin:0">NEWSLETTER</h2>
        </div>
        <hr style="border:0;border-top:solid 1px #e2e2e2;width:90%;margin:30px auto" class="horizontal-line">
        <div style="max-width:90%;margin-left:auto;margin-right:auto;margin-top:40px" class="nomal-paragraph">
          <div style="margin-top:20px">{today} {query} 관련 주요 기사입니다.</div>
          <div style="margin-top:20px">{briefing}</div>
        </div>
        {content}
        <div align="center" style="padding-top:40px;padding-right:10px;padding-bottom:10px;padding-left:10px">
          <a href="https://k-enterworld.com" style="text-decoration-line: none; display: inline-block; color: rgb(255, 255, 255); background-color: rgb(0, 0, 0); border-radius: 60px; width: auto; border-width: 1px; border-style: solid; border-color: rgb(0, 0, 0); padding: 10px 25px;" target="_blank">Learn More</a>
        </div>
        <div style="text-align:center;">
          <a style="font-size:12px;color:silver" href="mailto:your@email.com?subject=Unsubscribe!&amp;body=I&nbsp;don't&nbsp;want&nbsp;to&nbsp;receive&nbsp;an&nbsp;email&nbsp;from&nbsp;your&nbsp;service!" target="_blank">Unsubscribe from emails</a>
        </div>
      </div>
    </div>
    """
    return newsletter

def send_email(subject, body, from_email, to_email, smtp_server, smtp_port, smtp_username, smtp_password):
    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(message)

# 테스트
if __name__ == "__main__":
    query = "UI+UX"
    num_articles = 5

    articles = get_naver_news(query, num_articles)
    summaries = summarize_articles(articles)

    newsletter = generate_newsletter(query, articles, summaries)

    # 이메일 발송 정보
    subject = f"{datetime.now().strftime('%m월 %d일')} {query} 관련 주요 기사"
    from_email = ""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = ""
    smtp_password = ""

    # 받는 사람 이메일 리스트 읽기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    xlsx_file = os.path.join(current_dir, "list.xlsx")
    to_emails = pd.read_excel(xlsx_file)["e-mail"].tolist()

    # 메일 발송
    for to_email in to_emails:
        send_email(subject, newsletter, from_email, to_email, smtp_server, smtp_port, smtp_username, smtp_password)