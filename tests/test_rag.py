"""Tests for src/rag.py."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src import storage
from src.models import Article
from src.rag import ensure_embeddings, rank_articles


@pytest.fixture
def article_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect article storage to a temporary directory."""
    store = tmp_path / "data"
    monkeypatch.setattr("src.storage.ARTICLE_STORE_PATH", store)
    return store


@pytest.fixture
def mock_embed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace embeddings.embed with deterministic vectors."""

    def _embed(text: str) -> list[float]:
        # Return simple deterministic vectors based on text content.
        if "question" in text.lower():
            return [1.0, 0.0, 0.0]
        if "apple" in text.lower():
            return [0.9, 0.1, 0.0]
        if "banana" in text.lower():
            return [0.1, 0.9, 0.0]
        return [0.0, 0.0, 1.0]

    monkeypatch.setattr("src.embeddings.is_available", lambda: True)
    monkeypatch.setattr("src.embeddings.embed", _embed)


def _make_article(
    article_store: Path,
    title: str,
    content: str,
    embedding: list[float] | None = None,
) -> Article:
    """Create and save an article, returning the model."""
    article = Article(
        id=f"id-{title}",
        bloomberg_ticker="TICKER",
        source_id="example",
        url="https://example.com",
        title=title,
        content=content,
        published_at=datetime(2026, 1, 1, 12, 0),
        fetched_at=datetime(2026, 1, 2, 12, 0),
        stored_path=storage.article_path("TICKER", "example", title),
        embedding=embedding,
    )
    storage.save_article(article)
    return article


def test_rank_articles_sorts_by_cosine_similarity(article_store: Path, mock_embed: None) -> None:
    apple = _make_article(article_store, "Apple news", "Apple content")
    banana = _make_article(article_store, "Banana news", "Banana content")

    result = rank_articles("question about apple", [apple, banana], top_k=2)

    assert [article.title for article in result] == ["Apple news", "Banana news"]


def test_rank_articles_assigns_relevance_scores(article_store: Path, mock_embed: None) -> None:
    apple = _make_article(article_store, "Apple news", "Apple content")
    banana = _make_article(article_store, "Banana news", "Banana content")

    result = rank_articles("question about apple", [apple, banana], top_k=2)

    assert result[0].relevance_score is not None
    assert 0.0 <= result[0].relevance_score <= 1.0
    assert result[1].relevance_score is not None
    assert 0.0 <= result[1].relevance_score <= 1.0
    assert result[0].relevance_score > result[1].relevance_score


def test_rank_articles_respects_top_k(article_store: Path, mock_embed: None) -> None:
    apple = _make_article(article_store, "Apple news", "Apple content")
    banana = _make_article(article_store, "Banana news", "Banana content")
    other = _make_article(article_store, "Other news", "Other content")

    result = rank_articles("question", [apple, banana, other], top_k=2)

    assert len(result) == 2


def test_rank_articles_returns_all_when_top_k_exceeds_count(
    article_store: Path, mock_embed: None
) -> None:
    apple = _make_article(article_store, "Apple news", "Apple content")
    banana = _make_article(article_store, "Banana news", "Banana content")

    result = rank_articles("question", [apple, banana], top_k=10)

    assert len(result) == 2


def test_rank_articles_falls_back_when_embed_fails(
    article_store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _failing_embed(_text: str) -> list[float]:
        raise RuntimeError("embedding unavailable")

    monkeypatch.setattr("src.embeddings.embed", _failing_embed)

    apple = _make_article(article_store, "Apple news", "Apple content")
    banana = _make_article(article_store, "Banana news", "Banana content")

    result = rank_articles("question", [apple, banana], top_k=2)

    assert result == [apple, banana]
    assert all(article.relevance_score is None for article in result)


def test_ensure_embeddings_reads_existing_embedding_from_storage(
    article_store: Path, mock_embed: None
) -> None:
    article = _make_article(article_store, "Stored embedding", "Content", embedding=[0.5, 0.5, 0.5])
    article.embedding = None

    ensure_embeddings([article])

    assert article.embedding == [0.5, 0.5, 0.5]


def test_ensure_embeddings_computes_and_persists_missing_vectors(
    article_store: Path, mock_embed: None
) -> None:
    article = _make_article(article_store, "Apple news", "Apple content")
    article.embedding = None

    ensure_embeddings([article])

    assert article.embedding is not None

    loaded = storage.load_article(article.stored_path)
    assert loaded.embedding == article.embedding


def test_ensure_embeddings_skips_articles_with_embeddings(
    article_store: Path, mock_embed: None
) -> None:
    article = _make_article(article_store, "Already embedded", "Content", embedding=[0.1, 0.2, 0.3])

    ensure_embeddings([article])

    assert article.embedding == [0.1, 0.2, 0.3]
