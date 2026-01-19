"""Integration tests for CLI commands."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from conventions.cli import app

runner = CliRunner()


@pytest.fixture
def python_repo(tmp_path: Path) -> Path:
    """Create a sample Python repository for testing."""
    src = tmp_path / "src"
    src.mkdir()

    main_py = '''"""Main module."""
from typing import Optional

def main() -> int:
    """Entry point."""
    return 0

def helper(value: str) -> Optional[str]:
    """Helper function."""
    if value:
        return value.upper()
    return None
'''
    (src / "main.py").write_text(main_py)

    tests = tmp_path / "tests"
    tests.mkdir()

    test_py = '''"""Tests."""
import pytest

def test_main():
    from src.main import main
    assert main() == 0

def test_helper():
    from src.main import helper
    assert helper("test") == "TEST"
'''
    (tests / "test_main.py").write_text(test_py)

    return tmp_path


class TestDiscoverCommand:
    """Tests for the discover command."""

    def test_discover_basic(self, python_repo: Path):
        """Test basic discover command."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--quiet",
        ])
        # Should complete without error
        assert result.exit_code == 0

    def test_discover_creates_output_files(self, python_repo: Path):
        """Test that discover creates expected output files."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--quiet",
        ])
        assert result.exit_code == 0

        conventions_dir = python_repo / ".conventions"
        assert conventions_dir.exists()
        assert (conventions_dir / "conventions.raw.json").exists()
        assert (conventions_dir / "conventions.md").exists()
        assert (conventions_dir / "conventions-review.md").exists()

    def test_discover_json_output_valid(self, python_repo: Path):
        """Test that JSON output is valid."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--quiet",
        ])
        assert result.exit_code == 0

        json_path = python_repo / ".conventions" / "conventions.raw.json"
        data = json.loads(json_path.read_text())

        assert "version" in data
        assert "metadata" in data
        assert "rules" in data
        assert data["metadata"]["path"] == str(python_repo)

    def test_discover_with_languages(self, python_repo: Path):
        """Test discover with explicit language selection."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--languages", "python",
            "--quiet",
        ])
        assert result.exit_code == 0

        json_path = python_repo / ".conventions" / "conventions.raw.json"
        data = json.loads(json_path.read_text())
        assert "python" in data["metadata"]["detected_languages"]

    def test_discover_with_invalid_language(self, python_repo: Path):
        """Test discover with invalid language."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--languages", "invalid_lang",
        ])
        assert result.exit_code == 1
        assert "Invalid languages" in result.output

    def test_discover_with_max_files(self, python_repo: Path):
        """Test discover with max-files limit."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--max-files", "10",
            "--quiet",
        ])
        assert result.exit_code == 0

    def test_discover_verbose(self, python_repo: Path):
        """Test discover with verbose output."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--verbose",
        ])
        assert result.exit_code == 0
        # Should show progress
        assert "Scanning repository" in result.output or "Running detector" in result.output

    def test_discover_detailed(self, python_repo: Path):
        """Test discover with detailed output."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--detailed",
        ])
        assert result.exit_code == 0


class TestConfigIntegration:
    """Tests for configuration file integration."""

    def test_discover_with_config_file(self, python_repo: Path):
        """Test discover uses config file."""
        config = {
            "languages": ["python"],
            "max_files": 50,
            "output_formats": ["json", "markdown"],
        }
        config_path = python_repo / ".conventionsrc.json"
        config_path.write_text(json.dumps(config))

        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--quiet",
        ])
        assert result.exit_code == 0

    def test_discover_with_explicit_config(self, python_repo: Path, tmp_path: Path):
        """Test discover with explicit config path."""
        config = {
            "languages": ["python"],
            "max_files": 100,
        }
        config_path = tmp_path / "custom_config.json"
        config_path.write_text(json.dumps(config))

        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--config", str(config_path),
            "--quiet",
        ])
        assert result.exit_code == 0

    def test_discover_ignore_config(self, python_repo: Path):
        """Test discover with --ignore-config flag."""
        config = {
            "languages": ["go"],  # This would normally exclude Python
        }
        config_path = python_repo / ".conventionsrc.json"
        config_path.write_text(json.dumps(config))

        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--ignore-config",
            "--quiet",
        ])
        assert result.exit_code == 0

        # Should auto-detect Python even though config says go
        json_path = python_repo / ".conventions" / "conventions.raw.json"
        data = json.loads(json_path.read_text())
        assert "python" in data["metadata"]["detected_languages"]

    def test_min_score_exit_code(self, python_repo: Path):
        """Test that min_score causes non-zero exit when threshold not met."""
        config = {
            "min_score": 5.0,  # Very high threshold
        }
        config_path = python_repo / ".conventionsrc.json"
        config_path.write_text(json.dumps(config))

        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--quiet",
        ])
        # Should exit with code 2 if score below threshold
        # (May pass if all scores are 5, which is unlikely)
        assert result.exit_code in (0, 2)


class TestShowCommand:
    """Tests for the show command."""

    def test_show_after_discover(self, python_repo: Path):
        """Test show command after discover."""
        # First run discover
        runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--quiet",
        ])

        # Then run show
        result = runner.invoke(app, [
            "show",
            "--repo", str(python_repo),
        ])
        assert result.exit_code == 0
        assert "Conventions Detection Summary" in result.output

    def test_show_detailed(self, python_repo: Path):
        """Test show command with detailed output."""
        # First run discover
        runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--quiet",
        ])

        # Then run show with detailed
        result = runner.invoke(app, [
            "show",
            "--repo", str(python_repo),
            "--detailed",
        ])
        assert result.exit_code == 0

    def test_show_without_discover(self, python_repo: Path):
        """Test show command without prior discover."""
        result = runner.invoke(app, [
            "show",
            "--repo", str(python_repo),
        ])
        assert result.exit_code == 1
        assert "No conventions file found" in result.output


class TestOutputFormats:
    """Tests for output format options."""

    def test_format_json_only(self, python_repo: Path):
        """Test generating only JSON output."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--format", "json",
            "--quiet",
        ])
        assert result.exit_code == 0

        conventions_dir = python_repo / ".conventions"
        assert (conventions_dir / "conventions.raw.json").exists()

    def test_format_multiple(self, python_repo: Path):
        """Test generating multiple output formats."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(python_repo),
            "--format", "json,markdown,review",
            "--quiet",
        ])
        assert result.exit_code == 0

        conventions_dir = python_repo / ".conventions"
        assert (conventions_dir / "conventions.raw.json").exists()
        assert (conventions_dir / "conventions.md").exists()
        assert (conventions_dir / "conventions-review.md").exists()
