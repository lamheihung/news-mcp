"""Local sentence-transformer embedding interface for RAG.

The embedding model is loaded lazily on the first call to :func:`embed` so that
importing this module does not trigger a network download or CPU load. If the
model cannot be loaded, :func:`is_available` returns ``False`` and :func:`embed`
raises a descriptive ``RuntimeError`` that callers can catch to fall back to
non-RAG behavior.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_model: Any | None = None
_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _load_model() -> Any:
    """Lazy-load the sentence-transformer model and cache it globally."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model %s", _model_name)
            _model = SentenceTransformer(_model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as exc:
            logger.exception("Failed to load embedding model %s", _model_name)
            raise RuntimeError(f"Failed to load embedding model {_model_name}: {exc}") from exc
    return _model


def is_available() -> bool:
    """Return whether the embedding model can be loaded.

    Returns:
        ``True`` if the model loads successfully, otherwise ``False``.
    """
    try:
        _load_model()
    except Exception:
        return False
    return True


def embed(text: str) -> list[float]:
    """Return the embedding vector for the given text.

    Args:
        text: The text to embed.

    Returns:
        A list of floats representing the embedding vector.

    Raises:
        RuntimeError: If the text cannot be embedded.
    """
    model = _load_model()
    try:
        vector = model.encode(text, convert_to_numpy=False, convert_to_tensor=True)
    except Exception as exc:
        logger.exception("Failed to embed text")
        raise RuntimeError(f"Failed to embed text: {exc}") from exc

    return [float(value) for value in vector]
