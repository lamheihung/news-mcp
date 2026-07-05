"""Configuration loader for developer-curated sources.

See architecture/001-architecture-design.md for the configuration contract.
"""

import logging
from pathlib import Path

import yaml

from src.models import Source

logger = logging.getLogger(__name__)


def load_config(path: Path) -> list[Source]:
    """Load and validate a config file into a list of Source models.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        A list of validated Source models.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the config file is malformed.
        ValidationError: If a source entry fails Pydantic validation.
    """
    if not path.exists():
        logger.error("Config file not found: %s", path)
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        logger.info("Config file is empty, returning no sources: %s", path)
        return []

    if not isinstance(data, dict):
        logger.error(
            "Config file must contain a mapping at the top level, got %s: %s",
            type(data).__name__,
            path,
        )
        raise ValueError(
            f"Config file must contain a mapping at the top level, got {type(data).__name__}"
        )

    sources_data = data.get("sources", [])
    if sources_data is None:
        logger.info("Config 'sources' is null, returning no sources: %s", path)
        return []

    if not isinstance(sources_data, list):
        logger.error(
            "'sources' must be a list, got %s: %s",
            type(sources_data).__name__,
            path,
        )
        raise ValueError(f"'sources' must be a list, got {type(sources_data).__name__}")

    sources = [Source(**source) for source in sources_data]
    logger.info("Loaded %d source(s) from %s", len(sources), path)
    return sources
