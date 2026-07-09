"""Tests for src/resolver.py."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.models import Company
from src.resolver import CompanyResolutionError, resolve_company
from src.watchlist import load_watchlist


@pytest.fixture
def watchlist_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the watchlist to a temporary file and return its path."""
    path = tmp_path / "watchlist.yaml"
    monkeypatch.setattr("src.resolver.WATCHLIST_PATH", path)
    return path


def _mock_client_with_payload(payload: dict[str, Any]) -> Any:
    mock_response: Any = MagicMock()
    mock_response.text = json.dumps(payload)
    mock_client: Any = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


def test_resolve_company_missing_api_key() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(CompanyResolutionError, match="GEMINI_API_KEY"):
            resolve_company("Apple")


def test_resolve_company_success(watchlist_path: Path) -> None:
    mock_client = _mock_client_with_payload(
        {
            "bloomberg_ticker": "AAPL US Equity",
            "name": "Apple Inc.",
            "aliases": ["Apple", "AAPL", "Apple Inc."],
        }
    )

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            company = resolve_company("Apple")

    assert isinstance(company, Company)
    assert company.bloomberg_ticker == "AAPL US Equity"
    assert company.name == "Apple Inc."
    assert "Apple" in company.aliases
    assert any(alias != "Apple" for alias in company.aliases)

    entries = load_watchlist(watchlist_path)
    assert len(entries) == 1
    assert entries[0].bloomberg_ticker == "AAPL US Equity"
    assert entries[0].name == "Apple Inc."


def test_resolve_company_api_error(watchlist_path: Path) -> None:
    mock_client: Any = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API error")

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            with pytest.raises(CompanyResolutionError, match="Gemini API error"):
                resolve_company("Apple")

    assert not watchlist_path.exists()


def test_resolve_company_unparseable_response() -> None:
    mock_response: Any = MagicMock()
    mock_response.text = "not valid json"

    mock_client: Any = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            with pytest.raises(CompanyResolutionError, match="Could not parse"):
                resolve_company("Apple")


def test_resolve_company_missing_fields() -> None:
    mock_response: Any = MagicMock()
    mock_response.text = json.dumps({"bloomberg_ticker": "AAPL US Equity"})

    mock_client: Any = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            with pytest.raises(CompanyResolutionError, match="missing valid 'name'"):
                resolve_company("Apple")


def test_resolve_company_strips_markdown_fences() -> None:
    payload = json.dumps(
        {
            "bloomberg_ticker": "AAPL US Equity",
            "name": "Apple Inc.",
            "aliases": ["Apple", "AAPL"],
        }
    )
    mock_response: Any = MagicMock()
    mock_response.text = f"```json\n{payload}\n```"

    mock_client: Any = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            company = resolve_company("Apple")

    assert company.bloomberg_ticker == "AAPL US Equity"
    assert company.name == "Apple Inc."
    assert "Apple" in company.aliases


def test_resolve_company_empty_response() -> None:
    mock_response: Any = MagicMock()
    mock_response.text = None

    mock_client: Any = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            with pytest.raises(CompanyResolutionError, match="empty"):
                resolve_company("Apple")


def test_resolve_company_response_not_dict() -> None:
    mock_response: Any = MagicMock()
    mock_response.text = json.dumps(["not", "a", "dict"])

    mock_client: Any = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            with pytest.raises(CompanyResolutionError, match="not a JSON object"):
                resolve_company("Apple")


def test_resolve_company_missing_ticker() -> None:
    mock_response: Any = MagicMock()
    mock_response.text = json.dumps({"name": "Apple Inc.", "aliases": ["Apple"]})

    mock_client: Any = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            with pytest.raises(CompanyResolutionError, match="bloomberg_ticker"):
                resolve_company("Apple")


def test_resolve_company_missing_aliases() -> None:
    mock_response: Any = MagicMock()
    mock_response.text = json.dumps({"bloomberg_ticker": "AAPL US Equity", "name": "Apple Inc."})

    mock_client: Any = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            with pytest.raises(CompanyResolutionError, match="aliases"):
                resolve_company("Apple")


def test_resolve_company_upserts_watchlist_entry(watchlist_path: Path) -> None:
    mock_client = _mock_client_with_payload(
        {
            "bloomberg_ticker": "AAPL US Equity",
            "name": "Apple Inc.",
            "aliases": ["Apple", "AAPL"],
        }
    )

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            resolve_company("Apple")

    entries = load_watchlist(watchlist_path)
    assert len(entries) == 1
    assert entries[0].bloomberg_ticker == "AAPL US Equity"
    assert entries[0].name == "Apple Inc."
    assert entries[0].aliases == ["Apple", "AAPL"]


def test_resolve_company_preserves_existing_watchlist_fields(watchlist_path: Path) -> None:
    watchlist_path.parent.mkdir(parents=True, exist_ok=True)
    watchlist_path.write_text(
        "companies:\n"
        "  - bloomberg_ticker: AAPL US Equity\n"
        "    name: Apple\n"
        "    aliases: [Apple]\n"
        "    search_terms:\n"
        "      pcwatch: [Apple, AAPL]\n"
        "    exhausted_before:\n"
        "      pcwatch: 2026-01-01\n",
        encoding="utf-8",
    )

    mock_client = _mock_client_with_payload(
        {
            "bloomberg_ticker": "AAPL US Equity",
            "name": "Apple Inc.",
            "aliases": ["Apple", "AAPL", "Apple Inc."],
        }
    )

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            resolve_company("Apple")

    entries = load_watchlist(watchlist_path)
    assert len(entries) == 1
    assert entries[0].name == "Apple Inc."
    assert entries[0].search_terms == {"pcwatch": ["Apple", "AAPL"]}
    assert entries[0].exhausted_before == {"pcwatch": date(2026, 1, 1)}
