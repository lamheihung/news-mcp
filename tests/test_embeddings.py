"""Tests for src/embeddings.py."""

import logging

import pytest

from src import embeddings


def test_import_does_not_load_model() -> None:
    """Importing the module must not download or load the model."""
    assert embeddings._model is None


def test_is_available_true() -> None:
    """The model should be available when sentence-transformers is installed."""
    assert embeddings.is_available() is True


def test_embed_returns_non_empty_float_vector() -> None:
    """embed() must return a non-empty vector of floats."""
    vector = embeddings.embed("test")

    assert isinstance(vector, list)
    assert len(vector) > 0
    assert all(isinstance(value, float) for value in vector)


def test_embed_is_deterministic() -> None:
    """Embedding the same text twice should yield the same vector."""
    vector1 = embeddings.embed("determinism test")
    vector2 = embeddings.embed("determinism test")

    assert vector1 == pytest.approx(vector2)


def test_model_cached_after_first_embed() -> None:
    """The loaded model instance must be reused across embed() calls."""
    cached = embeddings._model
    assert cached is not None

    embeddings.embed("cache verification")

    assert embeddings._model is cached


def test_embed_failure_is_logged_and_raised(caplog: pytest.LogCaptureFixture) -> None:
    """A failed encode() call must be logged and re-raised as RuntimeError."""
    original_model = embeddings._model
    try:
        embeddings._model = object()

        with caplog.at_level(logging.ERROR, logger="src.embeddings"):
            with pytest.raises(RuntimeError, match="Failed to embed text"):
                embeddings.embed("failure test")

        assert "Failed to embed text" in caplog.text
    finally:
        embeddings._model = original_model
