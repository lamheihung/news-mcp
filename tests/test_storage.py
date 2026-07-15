"""Tests for src/storage.py."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from src.models import Article, DateRange
from src.storage import (
    _title_hash,
    article_exists,
    article_path,
    list_cached_articles,
    load_article,
    save_article,
)


@pytest.fixture
def article_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect article storage to a temporary directory."""
    store = tmp_path / "data"
    monkeypatch.setattr("src.storage.ARTICLE_STORE_PATH", store)
    return store


class TestTitleHash:
    def test_same_title_produces_same_hash(self) -> None:
        assert _title_hash("title") == _title_hash("title")

    def test_different_titles_produce_different_hashes(self) -> None:
        assert _title_hash("title one") != _title_hash("title two")

    def test_hash_is_sixteen_character_hex(self) -> None:
        hash_value = _title_hash("some title")
        assert len(hash_value) == 16
        assert all(char in "0123456789abcdef" for char in hash_value)


class TestArticlePath:
    def test_path_includes_ticker_source_and_hash(self, article_store: Path) -> None:
        path = article_path("AAPL US Equity", "example", "Mock title")
        assert path.parent == article_store / "AAPL US Equity" / "example"
        assert path.name.endswith(".md")


class TestArticleExists:
    def test_returns_true_when_file_exists(self, article_store: Path) -> None:
        path = article_path("TICKER", "example", "title")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("content", encoding="utf-8")
        assert article_exists("TICKER", "example", "title") is True

    def test_returns_false_when_file_missing(self, article_store: Path) -> None:
        assert article_exists("TICKER", "example", "missing title") is False


class TestSaveArticle:
    def test_creates_parent_directories(self, article_store: Path) -> None:
        article = Article(
            id="id",
            bloomberg_ticker="TICKER",
            source_id="example",
            url="https://example.com",
            title="Title",
            content="Body",
            published_at=datetime(2026, 1, 1, 12, 0),
            fetched_at=datetime(2026, 1, 2, 12, 0),
            stored_path=article_path("TICKER", "example", "Title"),
        )
        save_article(article)
        assert article.stored_path.exists()

    def test_writes_markdown_with_yaml_frontmatter(self, article_store: Path) -> None:
        article = Article(
            id="article-id",
            bloomberg_ticker="TICKER",
            source_id="example",
            url="https://example.com/article",
            title="Article Title",
            content="Article body",
            published_at=datetime(2026, 1, 1, 12, 0),
            fetched_at=datetime(2026, 1, 2, 12, 0),
            stored_path=article_path("TICKER", "example", "Article Title"),
        )
        save_article(article)

        text = article.stored_path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "id: article-id\n" in text
        assert "title: Article Title\n" in text
        assert "url: https://example.com/article\n" in text
        assert "source: example\n" in text
        assert "published_at: '2026-01-01T12:00:00'\n" in text
        assert "fetched_at: '2026-01-02T12:00:00'\n" in text
        assert "bloomberg_ticker: TICKER\n" in text
        assert text.endswith("---\nArticle body\n")

    def test_uses_stored_path_when_set(self, article_store: Path) -> None:
        custom_path = article_store / "custom" / "path.md"
        article = Article(
            id="id",
            bloomberg_ticker="TICKER",
            source_id="example",
            url="https://example.com",
            title="Title",
            content="Body",
            published_at=datetime(2026, 1, 1),
            fetched_at=datetime(2026, 1, 2),
            stored_path=custom_path,
        )
        save_article(article)
        assert custom_path.exists()

    def test_writes_embedding_to_frontmatter(self, article_store: Path) -> None:
        article = Article(
            id="article-id",
            bloomberg_ticker="TICKER",
            source_id="example",
            url="https://example.com/article",
            title="Article Title",
            content="Article body",
            published_at=datetime(2026, 1, 1, 12, 0),
            fetched_at=datetime(2026, 1, 2, 12, 0),
            stored_path=article_path("TICKER", "example", "Article Title"),
            embedding=[0.1, 0.2, 0.3],
        )
        save_article(article)

        text = article.stored_path.read_text(encoding="utf-8")
        assert "embedding:\n- 0.1\n- 0.2\n- 0.3\n" in text

    def test_does_not_write_embedding_when_none(self, article_store: Path) -> None:
        article = Article(
            id="article-id",
            bloomberg_ticker="TICKER",
            source_id="example",
            url="https://example.com/article",
            title="Article Title",
            content="Article body",
            published_at=datetime(2026, 1, 1, 12, 0),
            fetched_at=datetime(2026, 1, 2, 12, 0),
            stored_path=article_path("TICKER", "example", "Article Title"),
        )
        save_article(article)

        text = article.stored_path.read_text(encoding="utf-8")
        assert "embedding:" not in text


class TestLoadArticle:
    def test_round_trip_reconstructs_article(self, article_store: Path) -> None:
        original = Article(
            id="article-id",
            bloomberg_ticker="TICKER",
            source_id="example",
            url="https://example.com/article",
            title="Article Title",
            content="Article body",
            published_at=datetime(2026, 1, 1, 12, 0),
            fetched_at=datetime(2026, 1, 2, 12, 0),
            stored_path=article_path("TICKER", "example", "Article Title"),
        )
        save_article(original)
        loaded = load_article(original.stored_path)

        assert loaded.id == original.id
        assert loaded.bloomberg_ticker == original.bloomberg_ticker
        assert loaded.source_id == original.source_id
        assert loaded.url == original.url
        assert loaded.title == original.title
        assert loaded.content == original.content
        assert loaded.published_at == original.published_at
        assert loaded.fetched_at == original.fetched_at
        assert loaded.stored_path == original.stored_path

    def test_round_trip_preserves_embedding(self, article_store: Path) -> None:
        original = Article(
            id="article-id",
            bloomberg_ticker="TICKER",
            source_id="example",
            url="https://example.com/article",
            title="Article Title",
            content="Article body",
            published_at=datetime(2026, 1, 1, 12, 0),
            fetched_at=datetime(2026, 1, 2, 12, 0),
            stored_path=article_path("TICKER", "example", "Article Title"),
            embedding=[0.1, 0.2, 0.3],
        )
        save_article(original)
        loaded = load_article(original.stored_path)

        assert loaded.embedding == [0.1, 0.2, 0.3]

    def test_loads_legacy_article_without_embedding(self, article_store: Path) -> None:
        path = article_path("TICKER", "example", "Legacy Title")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            "id: legacy-id\n"
            "title: Legacy Title\n"
            "url: https://example.com\n"
            "source: example\n"
            "published_at: '2026-01-01T12:00:00'\n"
            "fetched_at: '2026-01-02T12:00:00'\n"
            "bloomberg_ticker: TICKER\n"
            "---\n"
            "Legacy body",
            encoding="utf-8",
        )

        article = load_article(path)
        assert article.embedding is None
        assert article.title == "Legacy Title"

    def test_raises_when_frontmatter_is_missing(self, tmp_path: Path) -> None:
        path = tmp_path / "article.md"
        path.write_text("No frontmatter here", encoding="utf-8")
        with pytest.raises(ValueError, match="invalid article file"):
            load_article(path)

    def test_handles_content_without_trailing_newline(self, article_store: Path) -> None:
        path = article_path("TICKER", "example", "Title")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            "id: id\n"
            "title: Title\n"
            "url: https://example.com\n"
            "source: example\n"
            "published_at: '2026-01-01T12:00:00'\n"
            "fetched_at: '2026-01-02T12:00:00'\n"
            "bloomberg_ticker: TICKER\n"
            "---\n"
            "Body",
            encoding="utf-8",
        )
        article = load_article(path)
        assert article.content == "Body"


class TestListCachedArticles:
    def test_returns_empty_when_directory_missing(self, article_store: Path) -> None:
        date_range = DateRange(start=date(2026, 1, 1), end=date(2026, 12, 31))
        assert list_cached_articles("MISSING", "example", date_range) == []

    def test_includes_articles_within_range(self, article_store: Path) -> None:
        article = Article(
            id="id",
            bloomberg_ticker="TICKER",
            source_id="example",
            url="https://example.com",
            title="In range",
            content="Body",
            published_at=datetime(2026, 6, 15, 12, 0),
            fetched_at=datetime(2026, 6, 16, 12, 0),
            stored_path=article_path("TICKER", "example", "In range"),
        )
        save_article(article)

        date_range = DateRange(start=date(2026, 6, 1), end=date(2026, 6, 30))
        articles = list_cached_articles("TICKER", "example", date_range)
        assert len(articles) == 1
        assert articles[0].title == "In range"

    def test_excludes_articles_outside_range(self, article_store: Path) -> None:
        article = Article(
            id="id",
            bloomberg_ticker="TICKER",
            source_id="example",
            url="https://example.com",
            title="Out of range",
            content="Body",
            published_at=datetime(2025, 1, 1, 12, 0),
            fetched_at=datetime(2026, 1, 1, 12, 0),
            stored_path=article_path("TICKER", "example", "Out of range"),
        )
        save_article(article)

        date_range = DateRange(start=date(2026, 1, 1), end=date(2026, 12, 31))
        assert list_cached_articles("TICKER", "example", date_range) == []

    def test_sorts_by_published_at_descending(self, article_store: Path) -> None:
        for day in [1, 2, 3]:
            article = Article(
                id=f"id-{day}",
                bloomberg_ticker="TICKER",
                source_id="example",
                url=f"https://example.com/{day}",
                title=f"Day {day}",
                content="Body",
                published_at=datetime(2026, 1, day, 12, 0),
                fetched_at=datetime(2026, 1, day, 12, 0),
                stored_path=article_path("TICKER", "example", f"Day {day}"),
            )
            save_article(article)

        date_range = DateRange(start=date(2026, 1, 1), end=date(2026, 1, 31))
        articles = list_cached_articles("TICKER", "example", date_range)
        assert [article.title for article in articles] == ["Day 3", "Day 2", "Day 1"]

    def test_works_when_start_equals_end(self, article_store: Path) -> None:
        article = Article(
            id="id",
            bloomberg_ticker="TICKER",
            source_id="example",
            url="https://example.com",
            title="Exact day",
            content="Body",
            published_at=datetime(2026, 6, 15, 0, 0),
            fetched_at=datetime(2026, 6, 15, 0, 0),
            stored_path=article_path("TICKER", "example", "Exact day"),
        )
        save_article(article)

        date_range = DateRange(start=date(2026, 6, 15), end=date(2026, 6, 15))
        articles = list_cached_articles("TICKER", "example", date_range)
        assert len(articles) == 1
