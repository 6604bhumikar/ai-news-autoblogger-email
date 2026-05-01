from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

import requests
import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

APP_TITLE = "AI News Auto-Blogger & Email Automation"
SERPAPI_URL = "https://serpapi.com/search.json"

st.set_page_config(page_title=APP_TITLE, page_icon=":newspaper:", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top right, #23311f 0, #101817 34%, #070b10 100%);
        color: #e7edf5;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111927 0%, #0a0f16 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.18);
    }
    .hero {
        padding: 28px 30px;
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 14px;
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.16), rgba(15, 23, 42, 0.90));
        box-shadow: 0 18px 48px rgba(0, 0, 0, 0.28);
        margin-bottom: 20px;
    }
    .hero h1 {
        color: #f8fafc;
        font-size: 2.05rem;
        margin: 0 0 8px;
        letter-spacing: 0;
    }
    .hero p {
        color: #b7c4d4;
        font-size: 1.02rem;
        margin: 0;
        max-width: 880px;
    }
    .metric-card {
        padding: 16px 18px;
        border: 1px solid rgba(148, 163, 184, 0.20);
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.72);
    }
    .metric-label {
        color: #91a3b8;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .section-note {
        color: #9fb0c5;
        font-size: 0.92rem;
        margin-top: -8px;
        margin-bottom: 14px;
    }
    textarea, input {
        color: #e5eef9 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(148, 163, 184, 0.22);
        background: rgba(15, 23, 42, 0.54);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_secret(name: str, default: Any = "") -> Any:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def has_secret(name: str) -> bool:
    value = get_secret(name, "")
    return bool(str(value).strip())


def build_llm() -> ChatGroq | None:
    api_key = str(get_secret("GROQ_API_KEY", "")).strip()
    if not api_key:
        return None
    return ChatGroq(api_key=api_key, model="llama3-70b-8192", temperature=0.4)


def fetch_ai_news(query: str, limit: int) -> list[dict[str, str]]:
    api_key = str(get_secret("SERPAPI_API_KEY", "")).strip()
    if not api_key:
        raise RuntimeError("Missing SERPAPI_API_KEY in Streamlit secrets.")

    params = {
        "engine": "google_news",
        "q": query,
        "api_key": api_key,
        "hl": "en",
        "gl": "us",
    }
    response = requests.get(SERPAPI_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    raw_items = payload.get("news_results", [])[:limit]

    articles: list[dict[str, str]] = []
    for item in raw_items:
        title = str(item.get("title", "")).strip()
        link = str(item.get("link", "")).strip()
        source = item.get("source", {})
        if isinstance(source, dict):
            source_name = str(source.get("name", "")).strip()
        else:
            source_name = str(source).strip()
        snippet = str(item.get("snippet") or item.get("summary") or "").strip()
        date = str(item.get("date", "")).strip()
        if title and link:
            articles.append({"title": title, "link": link, "source": source_name, "snippet": snippet, "date": date})
    return articles


def format_articles_for_prompt(articles: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for index, article in enumerate(articles, start=1):
        lines.append(
            f"{index}. Title: {article['title']}\n"
            f"   Source: {article.get('source', '')}\n"
            f"   Date: {article.get('date', '')}\n"
            f"   Snippet: {article.get('snippet', '')}\n"
            f"   Link: {article['link']}"
        )
    return "\n".join(lines)


def generate_blog_and_email(llm: ChatGroq, articles: list[dict[str, str]], tone: str) -> tuple[str, str, str]:
    article_context = format_articles_for_prompt(articles)
    messages = [
        SystemMessage(
            content=(
                "You are an AI technology blogger and email newsletter writer. "
                "Use only the provided article context. Do not invent facts. "
                "Include source links in the blog post."
            )
        ),
        HumanMessage(
            content=(
                f"Tone: {tone}\n\nNews articles:\n{article_context}\n\n"
                "Create three sections with these exact headings:\n"
                "EMAIL SUBJECT:\nBLOG POST:\nEMAIL BODY:\n\n"
                "The blog post should have a title, intro, key updates, and short conclusion. "
                "The email body should be concise and suitable for sending to subscribers."
            )
        ),
    ]
    response = llm.invoke(messages)
    text = str(response.content).strip()
    return parse_generated_content(text)


def parse_generated_content(text: str) -> tuple[str, str, str]:
    subject = "Latest AI News Roundup"
    blog = text
    email_body = text

    if "EMAIL SUBJECT:" in text and "BLOG POST:" in text and "EMAIL BODY:" in text:
        subject_part = text.split("EMAIL SUBJECT:", 1)[1].split("BLOG POST:", 1)[0]
        blog_part = text.split("BLOG POST:", 1)[1].split("EMAIL BODY:", 1)[0]
        email_part = text.split("EMAIL BODY:", 1)[1]
        subject = subject_part.strip().strip('"') or subject
        blog = blog_part.strip() or blog
        email_body = email_part.strip() or email_body

    return subject, blog, email_body


def send_email(recipient: str, subject: str, body: str) -> None:
    host = str(get_secret("SMTP_HOST", "smtp.gmail.com")).strip()
    port = int(get_secret("SMTP_PORT", 587))
    username = str(get_secret("SMTP_USER", "")).strip()
    password = str(get_secret("SMTP_PASSWORD", "")).strip()

    missing = [name for name, value in [("SMTP_USER", username), ("SMTP_PASSWORD", password)] if not value]
    if missing:
        raise RuntimeError(f"Missing email secret(s): {', '.join(missing)}")

    message = EmailMessage()
    message["From"] = username
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(message)


st.markdown(
    """
    <div class="hero">
        <h1>AI News Auto-Blogger & Email Automation</h1>
        <p>Monitor current AI news, generate a polished blog article with Groq, prepare a newsletter email, and send it through a configured SMTP account.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Automation Console")
    for secret_name in ["SERPAPI_API_KEY", "GROQ_API_KEY", "SMTP_USER", "SMTP_PASSWORD"]:
        if has_secret(secret_name):
            st.success(f"{secret_name} loaded")
        else:
            st.warning(f"{secret_name} missing")
    st.divider()
    st.markdown("**Workflow:** News API -> Groq writer -> email formatter -> SMTP delivery")
    st.markdown("**Safety:** Preview and edit content before sending.")
    st.caption("Use Gmail app passwords or another SMTP provider. Never place real secrets in source code.")

query_col, options_col = st.columns([1.5, 1])
with query_col:
    query = st.text_input("News search query", value="latest artificial intelligence news")
with options_col:
    limit = st.slider("Number of articles", min_value=3, max_value=10, value=5)
    tone = st.selectbox("Writing tone", ["Professional", "Student-friendly", "Executive", "Casual"], index=0)

metric_cols = st.columns(4)
metrics = [
    ("News Source", "SerpAPI"),
    ("Writer Model", "Groq Llama 3"),
    ("Delivery", "SMTP Email"),
    ("Articles", str(limit)),
]
for col, (label, value) in zip(metric_cols, metrics):
    with col:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

if "articles" not in st.session_state:
    st.session_state.articles = []
if "subject" not in st.session_state:
    st.session_state.subject = "Latest AI News Roundup"
if "blog" not in st.session_state:
    st.session_state.blog = ""
if "email_body" not in st.session_state:
    st.session_state.email_body = ""

fetch_col, generate_col = st.columns([1, 1])
with fetch_col:
    if st.button("Fetch Latest AI News", type="primary"):
        try:
            with st.spinner("Fetching AI news from SerpAPI..."):
                st.session_state.articles = fetch_ai_news(query, limit)
            if not st.session_state.articles:
                st.warning("No news articles were returned for this query.")
        except Exception as exc:
            st.error(f"News fetch failed: {exc}")

with generate_col:
    generate_disabled = not st.session_state.articles
    if st.button("Generate Blog + Email", disabled=generate_disabled):
        llm = build_llm()
        if llm is None:
            st.error("Missing GROQ_API_KEY in Streamlit secrets.")
        else:
            try:
                with st.spinner("Generating blog article and email copy..."):
                    subject, blog, email_body = generate_blog_and_email(llm, st.session_state.articles, tone)
                    st.session_state.subject = subject
                    st.session_state.blog = blog
                    st.session_state.email_body = email_body
            except Exception as exc:
                st.error(f"Generation failed: {exc}")

if st.session_state.articles:
    st.subheader("Fetched AI News")
    st.markdown('<div class="section-note">Source articles selected for the blog and newsletter generation.</div>', unsafe_allow_html=True)
    for article in st.session_state.articles:
        with st.container(border=True):
            st.markdown(f"**[{article['title']}]({article['link']})**")
            meta = " | ".join(part for part in [article.get("source", ""), article.get("date", "")] if part)
            if meta:
                st.caption(meta)
            if article.get("snippet"):
                st.write(article["snippet"])

st.subheader("Generated Blog Post")
st.markdown('<div class="section-note">Editable article draft created from the fetched news context.</div>', unsafe_allow_html=True)
st.session_state.blog = st.text_area("Blog post", value=st.session_state.blog, height=340)

st.subheader("Email Preview")
st.markdown('<div class="section-note">Review the subject, recipient, and body before sending.</div>', unsafe_allow_html=True)
st.session_state.subject = st.text_input("Email subject", value=st.session_state.subject)
default_recipient = str(get_secret("DEFAULT_RECIPIENT", "")).strip()
recipient = st.text_input("Recipient email", value=default_recipient)
st.session_state.email_body = st.text_area("Email body", value=st.session_state.email_body, height=220)

send_ready = bool(recipient.strip() and st.session_state.subject.strip() and st.session_state.email_body.strip())
if st.button("Send Email", disabled=not send_ready):
    try:
        with st.spinner("Sending email..."):
            send_email(recipient.strip(), st.session_state.subject.strip(), st.session_state.email_body.strip())
        st.success(f"Email sent to {recipient.strip()}.")
    except Exception as exc:
        st.error(f"Email send failed: {exc}")
