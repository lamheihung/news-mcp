"""Article storage helpers."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import yaml

from src.models import Article, DateRange

ARTICLE_STORE_PATH = Path("data")


def _title_hash(title: str) -> str:
    """Return a 16-character hex hash of the title."""
    return hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]


def article_path(ticker: str, source_id: str, title: str) -> Path:
    """Return the deterministic local path for an article."""
    return ARTICLE_STORE_PATH / ticker / source_id / f"{_title_hash(title)}.md"


def article_exists(ticker: str, source_id: str, title: str) -> bool:
    """Return True if the article file already exists locally."""
    return article_path(ticker, source_id, title).exists()


def save_article(article: Article) -> None:
    """Save an article as Markdown with YAML frontmatter."""
    path = article.stored_path or article_path(
        article.bloomberg_ticker, article.source_id, article.title
    )
    path.parent.mkdir(parents=True, exist_ok=True)

    frontmatter = {
        "id": article.id,
        "title": article.title,
        "url": article.url,
        "source": article.source_id,
        "published_at": article.published_at.isoformat(),
        "fetched_at": article.fetched_at.isoformat(),
        "bloomberg_ticker": article.bloomberg_ticker,
    }
    body = (
        "---\n"
        f"{yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)}"
        "---\n"
        f"{article.content}\n"
    )
    path.write_text(body, encoding="utf-8")
    article.stored_path = path


def load_article(path: Path) -> Article:
    """Load an article from a Markdown file with YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"invalid article file (missing frontmatter): {path}")

    _, frontmatter_text, content = text.split("---\n", 2)
    frontmatter = yaml.safe_load(frontmatter_text)

    return Article(
        id=frontmatter["id"],
        bloomberg_ticker=frontmatter["bloomberg_ticker"],
        source_id=frontmatter["source"],
        url=frontmatter["url"],
        title=frontmatter["title"],
        content=content.rstrip("\n"),
        published_at=datetime.fromisoformat(frontmatter["published_at"]),
        fetched_at=datetime.fromisoformat(frontmatter["fetched_at"]),
        stored_path=path,
    )


def list_cached_articles(ticker: str, source_id: str, date_range: DateRange) -> list[Article]:
    """Return cached articles for a ticker/source whose dates fall within date_range."""
    directory = ARTICLE_STORE_PATH / ticker / source_id
    if not directory.exists():
        return []

    articles = []
    for path in directory.glob("*.md"):
        article = load_article(path)
        published_date = article.published_at.date()
        if date_range.start <= published_date <= date_range.end:
            articles.append(article)

    return sorted(articles, key=lambda article: article.published_at, reverse=True)
