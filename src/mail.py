import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TypedDict


class SMTPTarget(TypedDict):
    host: str
    port: int
    use_tls: bool


SMTP_TEMPLATES: dict[str, SMTPTarget] = {
    "gmail": {
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": True,
    },
    "daouoffice": {
        "host": "outbound.daouoffice.com",
        "port": 25,
        "use_tls": False,
    },
}


def send_email(
    provider: str,
    email: str,
    password: str,
    subject: str,
    body: str,
    to_emails: list[str],
):
    if not to_emails:
        raise ValueError("수신자(to_emails)는 최소 1명 이상이어야 합니다.")

    template = SMTP_TEMPLATES.get(provider)
    if not template:
        raise ValueError(f"지원하지 않는 SMTP provider입니다: {provider}")

    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = email
    message["To"] = ", ".join(to_emails)

    message.attach(MIMEText(body, "html"))

    with smtplib.SMTP(template["host"], template["port"]) as server:
        if template["use_tls"]:
            server.starttls()
        server.login(email, password)
        server.send_message(message)
