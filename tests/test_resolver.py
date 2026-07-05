"""Tests for src/resolver.py."""

from __future__ import annotations

import json
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.models import Company
from src.resolver import CompanyResolutionError, resolve_company


def test_resolve_company_missing_api_key() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(CompanyResolutionError, match="GEMINI_API_KEY"):
            resolve_company("Apple")


def test_resolve_company_success() -> None:
    mock_response: Any = MagicMock()
    mock_response.text = json.dumps(
        {
            "bloomberg_ticker": "AAPL US Equity",
            "name": "Apple Inc.",
            "aliases": ["Apple", "AAPL", "Apple Inc."],
        }
    )

    mock_client: Any = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            company = resolve_company("Apple")

    assert isinstance(company, Company)
    assert company.bloomberg_ticker == "AAPL US Equity"
    assert company.name == "Apple Inc."
    assert "Apple" in company.aliases
    assert any(alias != "Apple" for alias in company.aliases)


def test_resolve_company_api_error() -> None:
    mock_client: Any = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API error")

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("src.resolver.genai.Client", return_value=mock_client):
            with pytest.raises(CompanyResolutionError, match="Gemini API error"):
                resolve_company("Apple")


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
