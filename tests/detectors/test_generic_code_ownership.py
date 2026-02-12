"""Tests for code ownership detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext
from conventions.detectors.generic.code_ownership import CodeOwnershipDetector


@pytest.fixture
def codeowners_repo(tmp_path: Path) -> Path:
    """Create a repo with CODEOWNERS."""
    github = tmp_path / ".github"
    github.mkdir()
    (github / "CODEOWNERS").write_text(
        "# Global owners\n"
        "* @org/platform-team\n"
        "\n"
        "# Frontend\n"
        "/src/frontend/ @org/frontend-team @alice\n"
        "\n"
        "# Backend\n"
        "/src/api/ @org/backend-team @bob\n"
        "\n"
        "# Infra\n"
        "*.yml @org/devops\n"
        "Dockerfile @org/devops\n"
    )
    return tmp_path


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a git repo with some history."""
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, capture_output=True,
    )

    # Create files and make multiple commits
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("v1")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "c1"], cwd=tmp_path, capture_output=True)

    for i in range(5):
        (src / "app.py").write_text(f"v{i+2}")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"c{i+2}"],
            cwd=tmp_path, capture_output=True,
        )

    (src / "utils.py").write_text("utils")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "add utils"], cwd=tmp_path, capture_output=True)

    return tmp_path


class TestCodeOwnershipDetector:
    """Tests for CodeOwnershipDetector."""

    def test_detects_codeowners(self, codeowners_repo: Path):
        """Detects CODEOWNERS rules and owners."""
        ctx = DetectorContext(repo_root=codeowners_repo, selected_languages=set(), max_files=100)
        result = CodeOwnershipDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.code_owners"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["rule_count"] == 5
        assert rule.stats["owner_count"] >= 4
        assert "@org/platform-team" in rule.stats["owners"]
        assert "@alice" in rule.stats["owners"]

    def test_detects_file_hotspots(self, git_repo: Path):
        """Detects frequently changed files."""
        ctx = DetectorContext(repo_root=git_repo, selected_languages=set(), max_files=100)
        result = CodeOwnershipDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.file_hotspots"]
        assert len(rules) == 1
        rule = rules[0]
        hotspots = rule.stats["hotspots"]
        assert hotspots[0]["file"] == "src/app.py"
        assert hotspots[0]["changes"] >= 5

    def test_no_rules_on_empty_repo(self, tmp_path: Path):
        """No rules emitted when no ownership patterns found."""
        ctx = DetectorContext(repo_root=tmp_path, selected_languages=set(), max_files=100)
        result = CodeOwnershipDetector().detect(ctx)
        # May have no rules, or only hotspots if tmp_path happens to be inside a git repo
        code_owner_rules = [r for r in result.rules if r.id == "generic.conventions.code_owners"]
        assert len(code_owner_rules) == 0
