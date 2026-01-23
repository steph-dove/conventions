"""Tests for configuration loading and management."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from conventions.config import (
    CONFIG_FILE_NAMES,
    ConventionsConfig,
    find_config_file,
    load_config,
    save_config,
)


class TestConventionsConfig:
    """Tests for ConventionsConfig dataclass."""

    def test_default_values(self, default_config: ConventionsConfig):
        """Test default configuration values."""
        assert default_config.languages is None
        assert default_config.max_files == 2000
        assert default_config.disabled_detectors == []
        assert default_config.disabled_rules == []
        assert default_config.output_formats == ["json", "markdown", "review"]
        assert default_config.exclude_patterns == []
        assert default_config.plugin_paths == []
        assert default_config.min_score is None

    def test_custom_values(self, custom_config: ConventionsConfig):
        """Test custom configuration values."""
        assert custom_config.languages == ["python", "go"]
        assert custom_config.max_files == 1000
        assert "python_graphql" in custom_config.disabled_detectors
        assert "python.conventions.graphql" in custom_config.disabled_rules
        assert "html" in custom_config.output_formats
        assert "**/generated/**" in custom_config.exclude_patterns
        assert "./custom_rules.py" in custom_config.plugin_paths
        assert custom_config.min_score == 3.5

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "languages": ["python"],
            "max_files": 500,
            "disabled_detectors": ["test_detector"],
            "min_score": 4.0,
        }
        config = ConventionsConfig.from_dict(data)
        assert config.languages == ["python"]
        assert config.max_files == 500
        assert config.disabled_detectors == ["test_detector"]
        assert config.min_score == 4.0
        # Defaults for unspecified values
        assert config.disabled_rules == []
        assert config.output_formats == ["json", "markdown", "review"]

    def test_from_dict_empty(self):
        """Test creating config from empty dictionary."""
        config = ConventionsConfig.from_dict({})
        assert config.languages is None
        assert config.max_files == 2000

    def test_to_dict_minimal(self, default_config: ConventionsConfig):
        """Test converting default config to dict (should be minimal)."""
        data = default_config.to_dict()
        # Default config should produce empty dict (all defaults)
        assert data == {}

    def test_to_dict_custom(self, custom_config: ConventionsConfig):
        """Test converting custom config to dict."""
        data = custom_config.to_dict()
        assert data["languages"] == ["python", "go"]
        assert data["max_files"] == 1000
        assert "python_graphql" in data["disabled_detectors"]
        assert data["min_score"] == 3.5

    def test_merge_configs(self, default_config: ConventionsConfig, custom_config: ConventionsConfig):
        """Test merging two configurations."""
        merged = default_config.merge(custom_config)
        # Custom values should take precedence
        assert merged.languages == ["python", "go"]
        assert merged.max_files == 1000
        assert merged.min_score == 3.5
        # Lists should be combined
        assert "python_graphql" in merged.disabled_detectors

    def test_merge_preserves_base(self):
        """Test that merge preserves base values when other has defaults."""
        base = ConventionsConfig(
            languages=["python"],
            min_score=3.0,
        )
        other = ConventionsConfig()  # All defaults
        merged = base.merge(other)
        # Base values should be preserved
        assert merged.languages == ["python"]
        assert merged.min_score == 3.0


class TestFindConfigFile:
    """Tests for finding configuration files."""

    def test_find_conventionsrc_json(self, tmp_path: Path):
        """Test finding .conventionsrc.json."""
        config_path = tmp_path / ".conventionsrc.json"
        config_path.write_text("{}")
        found = find_config_file(tmp_path)
        assert found == config_path

    def test_find_conventionsrc(self, tmp_path: Path):
        """Test finding .conventionsrc (without extension)."""
        config_path = tmp_path / ".conventionsrc"
        config_path.write_text("{}")
        found = find_config_file(tmp_path)
        assert found == config_path

    def test_find_conventions_json(self, tmp_path: Path):
        """Test finding conventions.json."""
        config_path = tmp_path / "conventions.json"
        config_path.write_text("{}")
        found = find_config_file(tmp_path)
        assert found == config_path

    def test_priority_order(self, tmp_path: Path):
        """Test that .conventionsrc.json takes priority."""
        (tmp_path / ".conventionsrc.json").write_text('{"max_files": 100}')
        (tmp_path / "conventions.json").write_text('{"max_files": 200}')
        found = find_config_file(tmp_path)
        assert found.name == ".conventionsrc.json"

    def test_no_config_file(self, tmp_path: Path):
        """Test when no config file exists."""
        found = find_config_file(tmp_path)
        assert found is None


class TestLoadConfig:
    """Tests for loading configuration files."""

    def test_load_valid_config(self, config_file: Path):
        """Test loading a valid config file."""
        config = load_config(config_file.parent, config_file)
        assert config.languages == ["python"]
        assert config.max_files == 500
        assert config.min_score == 3.0

    def test_load_default_when_no_file(self, tmp_path: Path):
        """Test loading defaults when no config file exists."""
        config = load_config(tmp_path)
        assert config.languages is None
        assert config.max_files == 2000

    def test_load_explicit_path(self, tmp_path: Path):
        """Test loading from an explicit config path."""
        custom_path = tmp_path / "custom_config.json"
        custom_path.write_text('{"max_files": 999}')
        config = load_config(tmp_path, custom_path)
        assert config.max_files == 999

    def test_load_invalid_json(self, tmp_path: Path):
        """Test loading invalid JSON raises ValueError."""
        config_path = tmp_path / ".conventionsrc.json"
        config_path.write_text("not valid json")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_config(tmp_path, config_path)

    def test_load_missing_file(self, tmp_path: Path):
        """Test loading non-existent explicit file raises FileNotFoundError."""
        missing_path = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path, missing_path)


class TestSaveConfig:
    """Tests for saving configuration files."""

    def test_save_and_reload(self, tmp_path: Path, custom_config: ConventionsConfig):
        """Test saving and reloading config."""
        config_path = tmp_path / "test_config.json"
        save_config(custom_config, config_path)

        assert config_path.exists()
        loaded = load_config(tmp_path, config_path)
        assert loaded.languages == custom_config.languages
        assert loaded.max_files == custom_config.max_files
        assert loaded.min_score == custom_config.min_score

    def test_save_default_config(self, tmp_path: Path, default_config: ConventionsConfig):
        """Test saving default config produces minimal JSON."""
        config_path = tmp_path / "default.json"
        save_config(default_config, config_path)

        content = json.loads(config_path.read_text())
        # Default config should produce empty or minimal dict
        assert content == {}
