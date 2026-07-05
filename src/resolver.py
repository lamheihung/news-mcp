"""Company identifier resolution via Gemini API.

See architecture/001-architecture-design.md for the resolver contract.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from google import genai

from src.models import Company

GEMINI_MODEL = "gemini-3.5-flash"

logger = logging.getLogger(__name__)


class CompanyResolutionError(ValueError):
    """Raised when a company identifier cannot be resolved."""


def resolve_company(identifier: str) -> Company:
    """Normalize a company identifier to a Bloomberg ticker via Gemini.

    Args:
        identifier: Any common company name or ticker.

    Returns:
        A validated Company model.

    Raises:
        CompanyResolutionError: If the API key is missing, the API call fails,
            or the response cannot be parsed into a Company.
    """
    logger.debug("Resolving company identifier: %s", identifier)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is missing")
        raise CompanyResolutionError(
            "GEMINI_API_KEY environment variable is required to resolve companies"
        )

    client = genai.Client(api_key=api_key)
    prompt = _build_prompt(identifier)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
    except Exception as exc:
        logger.error("Gemini API error while resolving %r: %s", identifier, exc)
        raise CompanyResolutionError(f"Gemini API error: {exc}") from exc

    company = _parse_response(response.text, identifier)
    logger.info(
        "Resolved %r to %s (%s)",
        identifier,
        company.bloomberg_ticker,
        company.name,
    )
    return company


def _build_prompt(identifier: str) -> str:
    return (
        "You are a financial data assistant. Given a company identifier, return "
        "the canonical Bloomberg ticker, the company's legal or common name, and "
        "a list of common aliases (including the input identifier if it is not "
        "already the ticker or name).\n\n"
        "Respond ONLY with a JSON object in this exact format:\n"
        "{\n"
        '  "bloomberg_ticker": "AAPL US Equity",\n'
        '  "name": "Apple Inc.",\n'
        '  "aliases": ["Apple", "AAPL", "Apple Inc."]\n'
        "}\n\n"
        "Do not include markdown code fences, explanations, or any other text.\n\n"
        f"Company identifier: {identifier}"
    )


def _parse_response(text: str | None, identifier: str) -> Company:
    if text is None:
        logger.error("Gemini returned empty response for %r", identifier)
        raise CompanyResolutionError("Gemini response text is empty")
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data: Any = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error(
            "Could not parse Gemini response for %r as JSON: %s",
            identifier,
            exc,
        )
        raise CompanyResolutionError(f"Could not parse Gemini response as JSON: {exc}") from exc

    if not isinstance(data, dict):
        logger.error("Gemini response for %r is not a JSON object", identifier)
        raise CompanyResolutionError("Gemini response is not a JSON object")

    ticker = data.get("bloomberg_ticker")
    name = data.get("name")
    aliases = data.get("aliases")

    if not isinstance(ticker, str) or not ticker.strip():
        logger.error("Gemini response for %r missing valid 'bloomberg_ticker'", identifier)
        raise CompanyResolutionError("Gemini response missing valid 'bloomberg_ticker'")
    if not isinstance(name, str) or not name.strip():
        logger.error("Gemini response for %r missing valid 'name'", identifier)
        raise CompanyResolutionError("Gemini response missing valid 'name'")
    if not isinstance(aliases, list) or not all(isinstance(a, str) for a in aliases):
        logger.error("Gemini response for %r missing valid 'aliases' list", identifier)
        raise CompanyResolutionError("Gemini response missing valid 'aliases' list")

    normalized_aliases = [a.strip() for a in aliases if a.strip()]
    if identifier not in normalized_aliases:
        normalized_aliases.append(identifier)

    return Company(
        bloomberg_ticker=ticker.strip(),
        name=name.strip(),
        aliases=normalized_aliases,
    )
