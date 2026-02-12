"""Tests for task runner detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext
from conventions.detectors.generic.task_runners import TaskRunnerDetector


@pytest.fixture
def makefile_repo(tmp_path: Path) -> Path:
    """Create a repo with a Makefile."""
    (tmp_path / "Makefile").write_text(
        "# Build the project\n"
        "build:\n"
        "\tgo build ./...\n"
        "\n"
        "# Run tests\n"
        "test:\n"
        "\tgo test ./...\n"
        "\n"
        "lint:\n"
        "\tgolangci-lint run\n"
        "\n"
        ".PHONY: build test lint\n"
    )
    return tmp_path


@pytest.fixture
def package_json_repo(tmp_path: Path) -> Path:
    """Create a repo with package.json scripts."""
    (tmp_path / "package.json").write_text(
        '{\n'
        '  "name": "myapp",\n'
        '  "scripts": {\n'
        '    "dev": "next dev",\n'
        '    "build": "next build",\n'
        '    "test": "jest",\n'
        '    "lint": "eslint .",\n'
        '    "start": "next start"\n'
        '  }\n'
        '}\n'
    )
    return tmp_path


@pytest.fixture
def taskfile_repo(tmp_path: Path) -> Path:
    """Create a repo with Taskfile.yml."""
    (tmp_path / "Taskfile.yml").write_text(
        "version: '3'\n"
        "\n"
        "tasks:\n"
        "  build:\n"
        "    desc: Build the application\n"
        "    cmds:\n"
        "      - go build ./...\n"
        "  test:\n"
        "    desc: Run all tests\n"
        "    cmds:\n"
        "      - go test ./...\n"
        "  lint:\n"
        "    cmds:\n"
        "      - golangci-lint run\n"
    )
    return tmp_path


@pytest.fixture
def justfile_repo(tmp_path: Path) -> Path:
    """Create a repo with a justfile."""
    (tmp_path / "justfile").write_text(
        "# Build the project\n"
        "build:\n"
        "  cargo build\n"
        "\n"
        "# Run tests\n"
        "test:\n"
        "  cargo test\n"
        "\n"
        "lint:\n"
        "  cargo clippy\n"
    )
    return tmp_path


class TestTaskRunnerDetector:
    """Tests for TaskRunnerDetector."""

    def test_detects_makefile(self, makefile_repo: Path):
        """Detects Makefile targets."""
        ctx = DetectorContext(repo_root=makefile_repo, selected_languages=set(), max_files=100)
        result = TaskRunnerDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.task_runner"]
        assert len(rules) == 1
        rule = rules[0]
        assert "makefile" in rule.stats["runners_found"]
        targets = rule.stats["targets"]["makefile"]
        names = [t["name"] for t in targets]
        assert "build" in names
        assert "test" in names
        assert "lint" in names

    def test_makefile_target_descriptions(self, makefile_repo: Path):
        """Makefile targets capture preceding comment descriptions."""
        ctx = DetectorContext(repo_root=makefile_repo, selected_languages=set(), max_files=100)
        result = TaskRunnerDetector().detect(ctx)
        targets = result.rules[0].stats["targets"]["makefile"]
        build = next(t for t in targets if t["name"] == "build")
        assert build["description"] == "Build the project"

    def test_detects_package_json_scripts(self, package_json_repo: Path):
        """Detects package.json scripts."""
        ctx = DetectorContext(repo_root=package_json_repo, selected_languages=set(), max_files=100)
        result = TaskRunnerDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.task_runner"]
        assert len(rules) == 1
        targets = rules[0].stats["targets"]["package_json"]
        names = [t["name"] for t in targets]
        assert "dev" in names
        assert "build" in names
        assert "test" in names
        # Verify command is captured
        dev = next(t for t in targets if t["name"] == "dev")
        assert dev["command"] == "next dev"

    def test_detects_taskfile(self, taskfile_repo: Path):
        """Detects Taskfile.yml tasks."""
        ctx = DetectorContext(repo_root=taskfile_repo, selected_languages=set(), max_files=100)
        result = TaskRunnerDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.task_runner"]
        assert len(rules) == 1
        targets = rules[0].stats["targets"]["taskfile"]
        names = [t["name"] for t in targets]
        assert "build" in names
        assert "test" in names
        # Check description
        build = next(t for t in targets if t["name"] == "build")
        assert build["description"] == "Build the application"

    def test_detects_justfile(self, justfile_repo: Path):
        """Detects justfile recipes."""
        ctx = DetectorContext(repo_root=justfile_repo, selected_languages=set(), max_files=100)
        result = TaskRunnerDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.task_runner"]
        assert len(rules) == 1
        targets = rules[0].stats["targets"]["justfile"]
        names = [t["name"] for t in targets]
        assert "build" in names
        assert "test" in names
        assert "lint" in names

    def test_detects_multiple_runners(self, tmp_path: Path):
        """Detects multiple task runners in same repo."""
        (tmp_path / "Makefile").write_text("build:\n\tmake\n")
        (tmp_path / "package.json").write_text('{"scripts": {"dev": "vite"}}')

        ctx = DetectorContext(repo_root=tmp_path, selected_languages=set(), max_files=100)
        result = TaskRunnerDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.task_runner"]
        assert len(rules) == 1
        assert len(rules[0].stats["runners_found"]) == 2
        assert rules[0].stats["total_targets"] == 2

    def test_no_rules_on_empty_repo(self, tmp_path: Path):
        """No rules emitted when no task runners found."""
        ctx = DetectorContext(repo_root=tmp_path, selected_languages=set(), max_files=100)
        result = TaskRunnerDetector().detect(ctx)
        assert len(result.rules) == 0
