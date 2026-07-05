"""Configuration loader for developer-curated sources.

See architecture/001-architecture-design.md for the configuration contract.
"""

from pathlib import Path

import yaml

from src.models import Source


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
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return []

    if not isinstance(data, dict):
        raise ValueError(
            f"Config file must contain a mapping at the top level, got {type(data).__name__}"
        )

    sources_data = data.get("sources", [])
    if sources_data is None:
        return []

    if not isinstance(sources_data, list):
        raise ValueError(f"'sources' must be a list, got {type(sources_data).__name__}")

    return [Source(**source) for source in sources_data]
