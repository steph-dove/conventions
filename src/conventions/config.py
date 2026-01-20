"""Configuration file support for conventions detection."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ConventionsConfig:
    """Configuration for conventions detection."""

    languages: list[str] | None = None
    max_files: int = 2000
    disabled_detectors: list[str] = field(default_factory=list)
    disabled_rules: list[str] = field(default_factory=list)
    output_formats: list[str] = field(default_factory=lambda: ["json", "markdown", "review"])
    exclude_patterns: list[str] = field(default_factory=list)
    plugin_paths: list[str] = field(default_factory=list)
    min_score: float | None = None  # Exit non-zero if avg score below this

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConventionsConfig":
        """Create config from dictionary."""
        return cls(
            languages=data.get("languages"),
            max_files=data.get("max_files", 2000),
            disabled_detectors=data.get("disabled_detectors", []),
            disabled_rules=data.get("disabled_rules", []),
            output_formats=data.get("output_formats", ["json", "markdown", "review"]),
            exclude_patterns=data.get("exclude_patterns", []),
            plugin_paths=data.get("plugin_paths", []),
            min_score=data.get("min_score"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        result: dict[str, Any] = {}
        if self.languages is not None:
            result["languages"] = self.languages
        if self.max_files != 2000:
            result["max_files"] = self.max_files
        if self.disabled_detectors:
            result["disabled_detectors"] = self.disabled_detectors
        if self.disabled_rules:
            result["disabled_rules"] = self.disabled_rules
        if self.output_formats != ["json", "markdown", "review"]:
            result["output_formats"] = self.output_formats
        if self.exclude_patterns:
            result["exclude_patterns"] = self.exclude_patterns
        if self.plugin_paths:
            result["plugin_paths"] = self.plugin_paths
        if self.min_score is not None:
            result["min_score"] = self.min_score
        return result

    def merge(self, other: "ConventionsConfig") -> "ConventionsConfig":
        """Merge two configs, with 'other' taking precedence."""
        return ConventionsConfig(
            languages=other.languages if other.languages is not None else self.languages,
            max_files=other.max_files if other.max_files != 2000 else self.max_files,
            disabled_detectors=list(set(self.disabled_detectors) | set(other.disabled_detectors)),
            disabled_rules=list(set(self.disabled_rules) | set(other.disabled_rules)),
            output_formats=other.output_formats if other.output_formats != ["json", "markdown", "review"] else self.output_formats,
            exclude_patterns=list(set(self.exclude_patterns) | set(other.exclude_patterns)),
            plugin_paths=list(set(self.plugin_paths) | set(other.plugin_paths)),
            min_score=other.min_score if other.min_score is not None else self.min_score,
        )


CONFIG_FILE_NAMES = [
    ".conventionsrc.json",
    ".conventionsrc",
    "conventions.json",
]


def find_config_file(repo_root: Path) -> Path | None:
    """Find configuration file in repository root."""
    for name in CONFIG_FILE_NAMES:
        config_path = repo_root / name
        if config_path.exists() and config_path.is_file():
            return config_path
    return None


def load_config(repo_root: Path, config_path: Path | None = None) -> ConventionsConfig:
    """
    Load configuration from file.

    Args:
        repo_root: Repository root directory
        config_path: Optional explicit config file path

    Returns:
        ConventionsConfig instance (defaults if no config found)
    """
    target_path: Path | None
    if config_path is not None:
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        target_path = config_path
    else:
        target_path = find_config_file(repo_root)

    if target_path is None:
        return ConventionsConfig()

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ConventionsConfig.from_dict(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {target_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error loading config file {target_path}: {e}")


def save_config(config: ConventionsConfig, path: Path) -> None:
    """Save configuration to file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2)
        f.write("\n")
