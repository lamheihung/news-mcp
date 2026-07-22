"""Tests for src/watchlist.py."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from src.models import Company, WatchlistEntry
from src.watchlist import (
    _find_entry,
    clear_exhausted_before,
    get_exhausted_before,
    get_search_terms,
    load_watchlist,
    save_watchlist,
    set_exhausted_before,
    set_search_terms,
    upsert_company,
)


class TestLoadWatchlist:
    def test_creates_empty_file_when_missing(self, tmp_path: Path) -> None:
        path = tmp_path / "watchlist.yaml"
        entries = load_watchlist(path)
        assert entries == []
        assert path.exists()
        assert path.read_text(encoding="utf-8") == "companies: []\n"

    def test_loads_valid_watchlist(self, tmp_path: Path) -> None:
        path = tmp_path / "watchlist.yaml"
        path.write_text(
            "companies:\n"
            '  - bloomberg_ticker: "000660 KS Equity"\n'
            "    name: SK hynix\n"
            "    aliases: [SK Hynix]\n"
            "    search_terms:\n"
            "      pcwatch: [SK Hynix, Hynix]\n"
            "    exhausted_before:\n"
            "      pcwatch: 2026-01-01\n",
            encoding="utf-8",
        )

        entries = load_watchlist(path)
        assert len(entries) == 1
        assert entries[0].bloomberg_ticker == "000660 KS Equity"
        assert entries[0].name == "SK hynix"
        assert entries[0].aliases == ["SK Hynix"]
        assert entries[0].search_terms == {"pcwatch": ["SK Hynix", "Hynix"]}
        assert entries[0].exhausted_before == {"pcwatch": date(2026, 1, 1)}

    def test_returns_empty_list_when_file_is_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "watchlist.yaml"
        path.write_text("", encoding="utf-8")
        assert load_watchlist(path) == []

    def test_returns_empty_list_when_companies_missing(self, tmp_path: Path) -> None:
        path = tmp_path / "watchlist.yaml"
        path.write_text("other_key: []\n", encoding="utf-8")
        assert load_watchlist(path) == []

    def test_returns_empty_list_when_companies_null(self, tmp_path: Path) -> None:
        path = tmp_path / "watchlist.yaml"
        path.write_text("companies:\n", encoding="utf-8")
        assert load_watchlist(path) == []

    def test_raises_when_entry_missing_required_field(self, tmp_path: Path) -> None:
        path = tmp_path / "watchlist.yaml"
        path.write_text(
            "companies:\n"
            "  - bloomberg_ticker: missing-name\n"
            "    aliases: []\n"
            "    search_terms: {}\n",
            encoding="utf-8",
        )
        with pytest.raises(ValidationError):
            load_watchlist(path)


class TestSaveWatchlist:
    def test_saves_entries_to_yaml(self, tmp_path: Path) -> None:
        path = tmp_path / "watchlist.yaml"
        entries = [
            WatchlistEntry(
                bloomberg_ticker="AAPL US Equity",
                name="Apple Inc.",
                aliases=["Apple"],
                search_terms={"example": ["Apple"]},
                exhausted_before={"example": date(2026, 1, 1)},
            )
        ]
        save_watchlist(entries, path)

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["companies"][0]["bloomberg_ticker"] == "AAPL US Equity"
        assert data["companies"][0]["search_terms"] == {"example": ["Apple"]}
        assert data["companies"][0]["exhausted_before"] == {"example": "2026-01-01"}

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        path = tmp_path / "nested" / "dir" / "watchlist.yaml"
        save_watchlist([], path)
        assert path.exists()

    def test_round_trip_preserves_data(self, tmp_path: Path) -> None:
        path = tmp_path / "watchlist.yaml"
        original = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=["Alias"],
                search_terms={"source": ["term"]},
                exhausted_before={"source": date(2026, 6, 15)},
            )
        ]
        save_watchlist(original, path)
        loaded = load_watchlist(path)
        assert loaded == original

    def test_atomic_write_uses_temp_file(self, tmp_path: Path) -> None:
        path = tmp_path / "watchlist.yaml"
        save_watchlist([], path)
        assert not any(tmp_path.glob("*.tmp"))
        assert path.exists()


class TestFindEntry:
    def test_returns_matching_entry(self) -> None:
        entry = WatchlistEntry(
            bloomberg_ticker="TICKER",
            name="Name",
            aliases=[],
            search_terms={},
        )
        assert _find_entry([entry], "TICKER") is entry

    def test_returns_none_when_not_found(self) -> None:
        assert _find_entry([], "TICKER") is None


class TestUpsertCompany:
    def test_adds_new_company(self) -> None:
        company = Company(bloomberg_ticker="AAPL US Equity", name="Apple Inc.", aliases=["Apple"])
        entries = upsert_company([], company)

        assert len(entries) == 1
        assert entries[0].bloomberg_ticker == "AAPL US Equity"
        assert entries[0].name == "Apple Inc."
        assert entries[0].aliases == ["Apple"]
        assert entries[0].search_terms == {}
        assert entries[0].exhausted_before == {}

    def test_updates_name_and_aliases_for_existing_ticker(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="AAPL US Equity",
                name="Old Name",
                aliases=["Old"],
                search_terms={"example": ["Apple"]},
                exhausted_before={"example": date(2026, 1, 1)},
            )
        ]
        company = Company(
            bloomberg_ticker="AAPL US Equity",
            name="Apple Inc.",
            aliases=["Apple", "AAPL"],
        )
        upsert_company(entries, company)

        assert entries[0].name == "Apple Inc."
        assert entries[0].aliases == ["Apple", "AAPL"]

    def test_preserves_search_terms_and_exhausted_before(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="AAPL US Equity",
                name="Old Name",
                aliases=["Old"],
                search_terms={"example": ["Apple"]},
                exhausted_before={"example": date(2026, 1, 1)},
            )
        ]
        company = Company(
            bloomberg_ticker="AAPL US Equity",
            name="Apple Inc.",
            aliases=["Apple"],
        )
        upsert_company(entries, company)

        assert entries[0].search_terms == {"example": ["Apple"]}
        assert entries[0].exhausted_before == {"example": date(2026, 1, 1)}

    def test_copies_aliases_so_mutations_do_not_leak(self) -> None:
        aliases = ["Apple"]
        company = Company(
            bloomberg_ticker="AAPL US Equity",
            name="Apple Inc.",
            aliases=aliases,
        )
        entries = upsert_company([], company)
        aliases.append("AAPL")
        assert entries[0].aliases == ["Apple"]


class TestGetSearchTerms:
    def test_returns_terms_for_known_ticker_and_source(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={"pcwatch": ["term1", "term2"]},
            )
        ]
        assert get_search_terms(entries, "TICKER", "pcwatch") == ["term1", "term2"]

    def test_returns_empty_list_when_ticker_missing(self) -> None:
        assert get_search_terms([], "TICKER", "pcwatch") == []

    def test_returns_empty_list_when_source_missing(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={},
            )
        ]
        assert get_search_terms(entries, "TICKER", "pcwatch") == []


class TestGetExhaustedBefore:
    def test_returns_date_for_known_ticker_and_source(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={},
                exhausted_before={"pcwatch": date(2026, 1, 1)},
            )
        ]
        assert get_exhausted_before(entries, "TICKER", "pcwatch") == date(2026, 1, 1)

    def test_returns_none_when_ticker_missing(self) -> None:
        assert get_exhausted_before([], "TICKER", "pcwatch") is None

    def test_returns_none_when_source_missing(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={},
                exhausted_before={},
            )
        ]
        assert get_exhausted_before(entries, "TICKER", "pcwatch") is None


class TestSetExhaustedBefore:
    def test_sets_marker_for_existing_ticker(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={},
            )
        ]
        set_exhausted_before(entries, "TICKER", "pcwatch", date(2026, 1, 1))
        assert entries[0].exhausted_before == {"pcwatch": date(2026, 1, 1)}

    def test_overwrites_existing_marker(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={},
                exhausted_before={"pcwatch": date(2026, 1, 1)},
            )
        ]
        set_exhausted_before(entries, "TICKER", "pcwatch", date(2026, 6, 1))
        assert entries[0].exhausted_before == {"pcwatch": date(2026, 6, 1)}

    def test_raises_when_ticker_not_found(self) -> None:
        with pytest.raises(ValueError, match="company TICKER not found in watchlist"):
            set_exhausted_before([], "TICKER", "pcwatch", date(2026, 1, 1))


class TestSetSearchTerms:
    def test_replaces_terms_for_existing_ticker_and_source(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={"pcwatch": ["old"]},
            )
        ]
        set_search_terms(entries, "TICKER", "pcwatch", ["new1", "new2"])
        assert entries[0].search_terms == {"pcwatch": ["new1", "new2"]}

    def test_clears_exhaustion_marker_for_source(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={"pcwatch": ["term"]},
                exhausted_before={"pcwatch": date(2026, 1, 1)},
            )
        ]
        set_search_terms(entries, "TICKER", "pcwatch", ["new"])
        assert entries[0].exhausted_before == {}

    def test_copies_terms_so_mutations_do_not_leak(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={},
            )
        ]
        terms = ["term"]
        set_search_terms(entries, "TICKER", "pcwatch", terms)
        terms.append("leak")
        assert entries[0].search_terms == {"pcwatch": ["term"]}

    def test_raises_when_ticker_not_found(self) -> None:
        with pytest.raises(ValueError, match="company TICKER not found in watchlist"):
            set_search_terms([], "TICKER", "pcwatch", ["term"])


class TestClearExhaustedBefore:
    def test_removes_marker_for_existing_source(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={},
                exhausted_before={"pcwatch": date(2026, 1, 1)},
            )
        ]
        clear_exhausted_before(entries, "TICKER", "pcwatch")
        assert entries[0].exhausted_before == {}

    def test_is_noop_when_source_has_no_marker(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={},
                exhausted_before={},
            )
        ]
        clear_exhausted_before(entries, "TICKER", "pcwatch")
        assert entries[0].exhausted_before == {}

    def test_only_removes_marker_for_requested_source(self) -> None:
        entries = [
            WatchlistEntry(
                bloomberg_ticker="TICKER",
                name="Name",
                aliases=[],
                search_terms={},
                exhausted_before={
                    "pcwatch": date(2026, 1, 1),
                    "example": date(2026, 2, 1),
                },
            )
        ]
        clear_exhausted_before(entries, "TICKER", "pcwatch")
        assert entries[0].exhausted_before == {"example": date(2026, 2, 1)}

    def test_raises_when_ticker_not_found(self) -> None:
        with pytest.raises(ValueError, match="company TICKER not found in watchlist"):
            clear_exhausted_before([], "TICKER", "pcwatch")
