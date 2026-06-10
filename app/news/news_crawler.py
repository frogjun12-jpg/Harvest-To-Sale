import os
import re
import warnings
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.parse import quote_plus
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

from app.config import load_app_env

load_app_env()
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NEWS_DOC_PATH = PROJECT_ROOT / "rag_docs" / "fruit_news_2026.md"
NEWS_DOC_PATH = Path(os.getenv("NEWS_RAG_DOC_PATH", str(DEFAULT_NEWS_DOC_PATH)))
NEWS_MAX_ARTICLES = int(os.getenv("NEWS_MAX_ARTICLES", "20"))
NEWS_REQUEST_TIMEOUT = int(os.getenv("NEWS_REQUEST_TIMEOUT", "12"))
NEWS_QUERIES = [
    query.strip()
    for query in os.getenv(
        "NEWS_QUERIES",
        "사과 가격 과일 농산물,과일 가격 농산물 수급,사과 출하 저장 가격,농산물 도매시장 과일 가격",
    ).split(",")
    if query.strip()
]

RSS_URL = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


@dataclass
class NewsArticle:
    title: str
    source: str
    published_at: str
    url: str
    summary: str
    query: str


def clean_text(value: str) -> str:
    text = BeautifulSoup(unescape(value or ""), "html.parser").get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_date(value: str) -> str:
    try:
        return parsedate_to_datetime(value).strftime("%Y-%m-%d")
    except Exception:
        return "날짜 확인 필요"


def strip_source_suffix(title: str, source: str) -> str:
    if source and title.endswith(f" - {source}"):
        return title[: -len(source) - 3].strip()
    return title


def summarize_article(title: str, description: str) -> str:
    base = description or title
    sentences = re.split(r"(?<=[.!?。])\s+|(?<=다\.)\s+", base)
    summary = sentences[0].strip() if sentences and sentences[0].strip() else base
    summary = re.sub(r"\s+", " ", summary)
    if len(summary) > 180:
        summary = summary[:177].rstrip() + "..."
    if not summary.endswith((".", "다", "요", "...")):
        summary += "."
    return summary


def fetch_rss_items(query: str) -> list[NewsArticle]:
    url = RSS_URL.format(query=quote_plus(query))
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=NEWS_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    root = ElementTree.fromstring(response.content)

    articles: list[NewsArticle] = []
    for item in root.findall("./channel/item"):
        raw_title = clean_text(item.findtext("title", ""))
        source_node = item.find("source")
        source = clean_text(source_node.text if source_node is not None else "")
        title = strip_source_suffix(raw_title, source)
        description = clean_text(item.findtext("description", ""))
        link = clean_text(item.findtext("link", ""))
        published_at = parse_date(item.findtext("pubDate", ""))
        if not title or not link:
            continue
        articles.append(
            NewsArticle(
                title=title,
                source=source or "출처 확인 필요",
                published_at=published_at,
                url=link,
                summary=summarize_article(title, description),
                query=query,
            )
        )
    return articles


def collect_fruit_news(max_articles: int = NEWS_MAX_ARTICLES) -> list[NewsArticle]:
    articles: list[NewsArticle] = []
    seen_titles: set[str] = set()

    for query in NEWS_QUERIES:
        for article in fetch_rss_items(query):
            normalized_title = re.sub(r"\W+", "", article.title).lower()
            if normalized_title in seen_titles:
                continue
            seen_titles.add(normalized_title)
            articles.append(article)
            if len(articles) >= max_articles:
                return articles

    return articles


def keyword_count(articles: list[NewsArticle], keywords: tuple[str, ...]) -> int:
    text = "\n".join(f"{article.title} {article.summary}" for article in articles)
    return sum(text.count(keyword) for keyword in keywords)


def build_market_signals(articles: list[NewsArticle]) -> list[str]:
    if not articles:
        return ["수집된 뉴스가 없어 시장 신호를 판단할 수 없다."]

    signals = [
        (
            "가격 변동",
            keyword_count(articles, ("가격", "시세", "도매", "소매")),
            "가격 질문에는 최근 시세와 함께 기사에서 언급된 가격 압력을 같이 본다.",
        ),
        (
            "수급",
            keyword_count(articles, ("수급", "출하", "공급", "생산량", "재배면적")),
            "판매시기 판단에는 출하량과 공급 부족 또는 과잉 신호를 같이 본다.",
        ),
        (
            "기후",
            keyword_count(articles, ("기후", "폭염", "한파", "강우", "냉해", "이상기상")),
            "품질과 가격 변동성 판단에는 기후 리스크를 별도 변수로 본다.",
        ),
        (
            "저장·유통",
            keyword_count(articles, ("저장", "유통", "물류", "재고")),
            "보관 물량과 유통 흐름이 언급되면 단기 판매 판단에 반영한다.",
        ),
        (
            "수출·소비",
            keyword_count(articles, ("수출", "소비", "수요", "급식", "온라인")),
            "수요 확대 뉴스는 가격 방어 가능성으로 보되 품목별 차이를 확인한다.",
        ),
    ]
    return [
        f"{name}: 관련 언급 {count}건. {guidance}"
        for name, count, guidance in signals
    ]


def build_news_markdown(articles: list[NewsArticle]) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 과일 시장 뉴스 요약",
        "",
        f"업데이트 시각: {generated_at}",
        "",
        "이 문서는 뉴스 원문을 그대로 저장하지 않고, 과일 가격·수급·판매 판단에 필요한 내용만 요약해 RAG에 사용한다.",
        "",
        "## 시장 신호 요약",
        "",
    ]
    for signal in build_market_signals(articles):
        lines.append(f"- {signal}")

    lines.extend(["", "## 기사 요약", ""])
    for index, article in enumerate(articles, start=1):
        lines.extend(
            [
                f"{index}. {article.title}",
                f"   - 날짜: {article.published_at}",
                f"   - 출처: {article.source}",
                f"   - 요약: {article.summary}",
                f"   - 수집 검색어: {article.query}",
                f"   - 링크: {article.url}",
                "",
            ]
        )

    lines.extend(
        [
            "## 챗봇 답변 활용 기준",
            "",
            "- 뉴스는 가격 예측을 대체하지 않고, 시세예측과 재고 현황을 해석하는 보조 신호로 사용한다.",
            "- 판매시기 질문에는 가격 방향, 수급 압력, 기후 리스크, 수요 변화를 함께 고려한다.",
            "- 단순 재고·상품등록 질문에는 뉴스 내용으로 답변을 과하게 확장하지 않는다.",
            "- 링크는 출처 확인용이며, 답변에서는 사용자가 요청하지 않는 한 기사 링크를 길게 나열하지 않는다.",
            "",
        ]
    )
    return "\n".join(lines)


def crawl_and_save_fruit_news() -> Path:
    articles = collect_fruit_news()
    if not articles:
        raise RuntimeError("수집된 과일 뉴스가 없습니다.")

    NEWS_DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    NEWS_DOC_PATH.write_text(build_news_markdown(articles), encoding="utf-8")
    return NEWS_DOC_PATH


if __name__ == "__main__":
    path = crawl_and_save_fruit_news()
    print(path)
