import os
from datetime import datetime

from dotenv import load_dotenv

from src.article import Article, get_naver_news
from src.llm_provider import ClaudeProvider, LLMProvider, OpenAIProvider
from src.mail import send_email


def summarize_articles(client: LLMProvider, articles: list[Article]):
    summaries = []
    for article in articles:
        prompt = f"""
        다음 기사를 200자 내외로 인사와 '기사를 요약하겠다'는 내용은 제외하고 친절한 말투로 요약해주세요:
        제목: {article.title}
        본문: {article.content}
        """
        summary = client.create(prompt)
        summaries.append(summary)
    return summaries


def generate_newsletter(
    client: LLMProvider, query: str, articles: list[Article], summaries: list
):
    today = datetime.now().strftime("%m월 %d일")
    content = ""

    for article, summary in zip(articles, summaries):
        content += f"""
        <div style="max-width:90%;margin-left:auto;margin-right:auto;margin-top:40px" class="nomal-paragraph">
          <div style="font-weight:bold;font-size:18px;margin-bottom:10px">{article.title}</div>
          <div style="margin-top:20px">{summary}</div>
          <div style="margin-top:10px"><a href="{article.url}" target="_blank">{article.url}</a></div>
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


def send_news_letter(subject: str, body: str, to_emails: list[str]):
    provider = os.getenv("SMTP_PROVIDER")
    if not provider:
        raise EnvironmentError("SMTP_PROVIDER 정보가 존재하지 않습니다")
    email = os.getenv("SMTP_EMAIL")
    if not email:
        raise EnvironmentError("SMTP_EMAIL 정보가 존재하지 않습니다")
    password = os.getenv("SMTP_PASSWORD")
    if not password:
        raise EnvironmentError("SMTP_PASSWORD 정보가 존재하지 않습니다")

    send_email(
        provider=provider,
        email=email,
        password=password,
        subject=subject,
        body=body,
        to_emails=to_emails,
    )


# 테스트
if __name__ == "__main__":
    load_dotenv()
    # api_key = os.getenv("ANTHROPIC_API_KEY")
    # if not api_key:
    #     raise EnvironmentError("ANTHROPIC_API_KEY is not set")
    # client: LLMProvider = ClaudeProvider(api_key=api_key)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set")
    client: LLMProvider = OpenAIProvider(api_key=api_key)

    query = "UI+UX"
    num_articles = 1

    articles = get_naver_news(query, num_articles)
    summaries = summarize_articles(client, articles)

    newsletter = generate_newsletter(client, query, articles, summaries)
    print(newsletter)

    send_news_letter(
        subject="new letter test",
        body=newsletter,
        to_emails=["test@email.com"],
    )
