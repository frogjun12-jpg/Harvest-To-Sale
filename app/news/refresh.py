from app.news.news_crawler import collect_fruit_news, crawl_and_save_fruit_news
from app.rag.ingest_docs import ingest_all


def refresh_news_rag() -> dict:
    news_path = crawl_and_save_fruit_news()
    ingest_all()

    return {
        "status": "ok",
        "news_doc_path": str(news_path),
    }


def preview_news() -> dict:
    articles = collect_fruit_news(max_articles=5)
    return {
        "count": len(articles),
        "articles": [
            {
                "title": article.title,
                "source": article.source,
                "published_at": article.published_at,
                "summary": article.summary,
                "url": article.url,
            }
            for article in articles
        ],
    }
