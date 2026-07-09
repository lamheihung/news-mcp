"""Dynamic scraper module loader."""

from __future__ import annotations

import importlib
from types import ModuleType

from src.scraper_base import BaseScraper


class ScraperLoadError(Exception):
    """Raised when a scraper module or class cannot be loaded."""


def load_scraper(module_name: str) -> ModuleType:
    """Dynamically import a scraper module registered in config.yaml."""
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise ScraperLoadError(f"scraper module not found: {module_name}") from exc


def _default_class_name(module_name: str) -> str:
    """Derive the conventional scraper class name from a module name."""
    last_segment = module_name.rsplit(".", 1)[-1]
    return f"{last_segment.capitalize()}Scraper"


def get_scraper_class(module: ModuleType, class_name: str | None = None) -> type[BaseScraper]:
    """Retrieve the scraper class from a loaded module by convention."""
    name = class_name or _default_class_name(module.__name__)
    try:
        cls = getattr(module, name)
    except AttributeError as exc:
        raise ScraperLoadError(f"scraper class not found in {module.__name__}: {name}") from exc

    if not isinstance(cls, type) or not issubclass(cls, BaseScraper):
        raise ScraperLoadError(f"{module.__name__}.{name} is not a BaseScraper subclass")

    return cls
