"""Integration tests for CLAUDE.md output format."""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from conventions.cli import app

runner = CliRunner()


@pytest.fixture
def node_repo(tmp_path: Path) -> Path:
    """Create a minimal Node.js repo for testing."""
    src = tmp_path / "src"
    src.mkdir()

    (src / "index.ts").write_text(
        'import express from "express";\n'
        "const app = express();\n"
        'app.get("/", (req, res) => res.send("ok"));\n'
        "export default app;\n"
    )

    (tmp_path / "package.json").write_text(
        '{\n'
        '  "name": "test-project",\n'
        '  "version": "1.0.0",\n'
        '  "scripts": { "test": "jest" },\n'
        '  "devDependencies": { "jest": "^29.0.0", "typescript": "^5.0.0" }\n'
        "}\n"
    )

    (tmp_path / "tsconfig.json").write_text(
        '{ "compilerOptions": { "strict": true, "target": "ES2020" } }\n'
    )

    return tmp_path


class TestClaudeFormatCli:
    """Tests for --format claude CLI integration."""

    def test_claude_format_creates_file(self, node_repo: Path):
        """Running --format claude creates CLAUDE.md at project root."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(node_repo),
            "--format", "claude",
            "--quiet",
        ])
        assert result.exit_code == 0

        claude_md = node_repo / "CLAUDE.md"
        assert claude_md.exists()

    def test_claude_format_output_has_sections(self, node_repo: Path):
        """CLAUDE.md output contains expected sections."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(node_repo),
            "--format", "claude",
            "--quiet",
        ])
        assert result.exit_code == 0

        content = (node_repo / "CLAUDE.md").read_text()
        assert "# CLAUDE.md" in content
        assert "## Project Overview" in content
        assert "## Tech Stack" in content
        assert "## Commands" in content
        assert "## Decision Log" in content
        assert "## Known Pitfalls" in content

    def test_claude_flag(self, node_repo: Path):
        """--claude writes to .claude/CLAUDE.md."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(node_repo),
            "--claude",
            "--quiet",
        ])
        assert result.exit_code == 0

        personal_path = node_repo / ".claude" / "CLAUDE.md"
        assert personal_path.exists()

        # Root should NOT have CLAUDE.md
        assert not (node_repo / "CLAUDE.md").exists()

    def test_claude_combined_with_other_formats(self, node_repo: Path):
        """Claude format can be combined with other formats."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(node_repo),
            "--format", "json,claude",
            "--quiet",
        ])
        assert result.exit_code == 0

        assert (node_repo / "CLAUDE.md").exists()
        assert (node_repo / ".conventions" / "conventions.raw.json").exists()

    def test_claude_format_verbose_shows_path(self, node_repo: Path):
        """Verbose mode shows the path where CLAUDE.md was written."""
        result = runner.invoke(app, [
            "discover",
            "--repo", str(node_repo),
            "--format", "claude",
        ])
        assert result.exit_code == 0
        assert "Wrote CLAUDE.md to:" in result.output
