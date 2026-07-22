"""Automatic watchlist helpers."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile

import yaml

from src.models import Company, WatchlistEntry


def load_watchlist(path: Path) -> list[WatchlistEntry]:
    """Load the watchlist from YAML, creating an empty file if missing."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("companies: []\n", encoding="utf-8")
        return []

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = data.get("companies", []) or []
    return [WatchlistEntry.model_validate(entry) for entry in entries]


def save_watchlist(entries: list[WatchlistEntry], path: Path) -> None:
    """Save the watchlist to YAML atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "companies": [entry.model_dump(mode="json") for entry in entries],
    }
    payload = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)

    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
    ) as tmp_file:
        tmp_file.write(payload)
        tmp_path = Path(tmp_file.name)

    tmp_path.replace(path)


def _find_entry(entries: list[WatchlistEntry], ticker: str) -> WatchlistEntry | None:
    for entry in entries:
        if entry.bloomberg_ticker == ticker:
            return entry
    return None


def upsert_company(entries: list[WatchlistEntry], company: Company) -> list[WatchlistEntry]:
    """Add or update a company entry while preserving search terms and exhaustion markers."""
    entry = _find_entry(entries, company.bloomberg_ticker)
    if entry is None:
        entries.append(
            WatchlistEntry(
                bloomberg_ticker=company.bloomberg_ticker,
                name=company.name,
                aliases=list(company.aliases),
                search_terms={},
                exhausted_before={},
            )
        )
    else:
        entry.name = company.name
        entry.aliases = list(company.aliases)
    return entries


def get_search_terms(entries: list[WatchlistEntry], ticker: str, source_id: str) -> list[str]:
    """Return search terms for a company and source, or an empty list."""
    entry = _find_entry(entries, ticker)
    if entry is None:
        return []
    return entry.search_terms.get(source_id, [])


def get_exhausted_before(entries: list[WatchlistEntry], ticker: str, source_id: str) -> date | None:
    """Return the exhaustion marker date for a company and source, or None."""
    entry = _find_entry(entries, ticker)
    if entry is None:
        return None
    return entry.exhausted_before.get(source_id)


def set_exhausted_before(
    entries: list[WatchlistEntry],
    ticker: str,
    source_id: str,
    value: date,
) -> list[WatchlistEntry]:
    """Set the exhaustion marker date for a company and source."""
    entry = _find_entry(entries, ticker)
    if entry is None:
        raise ValueError(f"company {ticker} not found in watchlist")
    entry.exhausted_before[source_id] = value
    return entries


def set_search_terms(
    entries: list[WatchlistEntry],
    ticker: str,
    source_id: str,
    terms: list[str],
) -> list[WatchlistEntry]:
    """Replace search terms for a company/source and clear its exhaustion marker."""
    entry = _find_entry(entries, ticker)
    if entry is None:
        raise ValueError(f"company {ticker} not found in watchlist")
    entry.search_terms[source_id] = list(terms)
    entry.exhausted_before.pop(source_id, None)
    return entries


def clear_exhausted_before(
    entries: list[WatchlistEntry],
    ticker: str,
    source_id: str,
) -> list[WatchlistEntry]:
    """Remove the exhaustion marker for a company and source."""
    entry = _find_entry(entries, ticker)
    if entry is None:
        raise ValueError(f"company {ticker} not found in watchlist")
    entry.exhausted_before.pop(source_id, None)
    return entries
