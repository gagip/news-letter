import os
from datetime import datetime

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.article import Article, get_naver_news
from src.llm_provider import ClaudeProvider, LLMProvider, OpenAIProvider
from src.mail import send_email

jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


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
    
    # 요약된 본문 전체를 다시 하나로 묶어서 브리핑하는 문단 생성
    prompt = f"""
    다음 기사 요약들을 하나로 묶어서 전체 뉴스레터에 대해 브리핑하는 문단을 300자 내외로 생성해주세요:

    기사 요약:
    {summaries}
    """
    briefing = client.create(prompt)

    # 각 기사에 대해 article block 렌더링
    article_block_template = jinja_env.get_template("article_block.html")
    article_blocks = [
        article_block_template.render(article=article, summary=summary)
        for article, summary in zip(articles, summaries)
    ]

    # 전체 뉴스레터 렌더링
    newsletter_template = jinja_env.get_template("newsletter.html")
    rendered_html = newsletter_template.render(
        today=today,
        query=query,
        briefing=briefing,
        article_blocks=article_blocks
    )

    return rendered_html


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
