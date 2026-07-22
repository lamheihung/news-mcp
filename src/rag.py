"""RAG ranking and embedding backfill for the Investment Research MCP Server."""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from src import embeddings, storage

if TYPE_CHECKING:
    from src.models import Article

logger = logging.getLogger(__name__)


def _cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """Return the cosine similarity between two vectors using pure Python."""
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b, strict=False))
    magnitude_a = math.sqrt(sum(value * value for value in vector_a))
    magnitude_b = math.sqrt(sum(value * value for value in vector_b))

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def ensure_embeddings(articles: list[Article]) -> list[Article]:
    """Compute and persist embeddings for articles that do not have one.

    Missing embeddings are first read from the cached article file; if the file
    does not contain an embedding, the article text is embedded and the file is
    rewritten with the new vector.
    """
    if not embeddings.is_available():
        logger.warning("Embedding model is not available; skipping embedding backfill")
        return articles

    for article in articles:
        if article.embedding is not None:
            continue

        try:
            cached = storage.load_article(article.stored_path)
            if cached.embedding is not None:
                article.embedding = cached.embedding
                continue
        except Exception:
            logger.exception("Failed to load cached article %s", article.stored_path)

        try:
            text = f"{article.title}\n\n{article.content}"
            article.embedding = embeddings.embed(text)
            storage.save_article(article)
        except Exception:
            logger.exception("Failed to embed article %s", article.id)

    return articles


def rank_articles(question: str, articles: list[Article], top_k: int) -> list[Article]:
    """Rank articles by cosine similarity to the question embedding.

    Args:
        question: The analyst's question.
        articles: Articles to rank.
        top_k: Maximum number of articles to return.

    Returns:
        Up to ``top_k`` articles sorted by descending relevance score. If
        embedding fails, the original articles are returned unchanged.
    """
    try:
        question_embedding = embeddings.embed(question)
        ranked_articles = list(ensure_embeddings(articles))
    except Exception:
        logger.exception("Failed to rank articles by relevance")
        return articles

    for article in ranked_articles:
        if article.embedding is not None:
            article.relevance_score = _cosine_similarity(question_embedding, article.embedding)
        else:
            article.relevance_score = 0.0

    ranked_articles.sort(key=lambda article: article.relevance_score or 0.0, reverse=True)
    return ranked_articles[:top_k]
