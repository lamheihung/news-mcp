"""Tests for the configuration loader in src/config.py."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from src.config import load_config
from src.models import Source


def test_load_config_returns_sources(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
sources:
  - id: reuters
    name: Reuters
    base_url: https://www.reuters.com
    scraper_module: scrapers.reuters
    description: Financial news
""",
        encoding="utf-8",
    )

    sources = load_config(config_path)
    assert len(sources) == 1
    assert isinstance(sources[0], Source)
    assert sources[0].id == "reuters"


def test_load_config_empty_sources(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("sources: []\n", encoding="utf-8")

    sources = load_config(config_path)
    assert sources == []


def test_load_config_missing_sources_key(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("{ }\n", encoding="utf-8")

    sources = load_config(config_path)
    assert sources == []


def test_load_config_empty_file(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("", encoding="utf-8")

    sources = load_config(config_path)
    assert sources == []


def test_load_config_null_sources(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("sources: null\n", encoding="utf-8")

    sources = load_config(config_path)
    assert sources == []


def test_load_config_missing_file(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"

    with pytest.raises(FileNotFoundError):
        load_config(config_path)


def test_load_config_malformed_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("sources: [\n", encoding="utf-8")

    with pytest.raises(yaml.YAMLError):
        load_config(config_path)


def test_load_config_sources_not_list(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("sources: not-a-list\n", encoding="utf-8")

    with pytest.raises(ValueError, match="'sources' must be a list"):
        load_config(config_path)


def test_load_config_top_level_not_mapping(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("- just\n- a\n- list\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a mapping"):
        load_config(config_path)


def test_load_config_missing_required_field(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
sources:
  - id: reuters
    name: Reuters
    base_url: https://www.reuters.com
""",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_config(config_path)
