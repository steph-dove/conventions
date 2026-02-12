"""Tests for dependency health detection."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext


class TestNodeDependencyHealth:
    """Tests for Node.js dependency health."""

    def test_detects_caret_pinning(self, tmp_path: Path):
        """Detects caret (^) pinning strategy."""
        from conventions.detectors.node.package_manager import NodePackageManagerDetector

        (tmp_path / "package.json").write_text(
            '{\n'
            '  "dependencies": {\n'
            '    "express": "^4.18.0",\n'
            '    "cors": "^2.8.5",\n'
            '    "helmet": "^7.0.0"\n'
            '  },\n'
            '  "devDependencies": {\n'
            '    "jest": "^29.0.0",\n'
            '    "typescript": "5.3.3"\n'
            '  }\n'
            '}\n'
        )
        (tmp_path / "package-lock.json").write_text("{}")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodePackageManagerDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.dependency_health"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["pinning_strategy"] == "caret"
        assert rule.stats["caret_count"] == 4
        assert rule.stats["exact_count"] == 1
        assert rule.stats["has_lock_file"] is True
        assert rule.stats["total_deps"] == 5

    def test_detects_engine_constraint(self, tmp_path: Path):
        """Detects engines field."""
        from conventions.detectors.node.package_manager import NodePackageManagerDetector

        (tmp_path / "package.json").write_text(
            '{\n'
            '  "engines": {"node": ">=20.0.0"},\n'
            '  "dependencies": {"express": "^4.18.0"}\n'
            '}\n'
        )

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodePackageManagerDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.dependency_health"]
        assert len(rules) == 1
        assert rules[0].stats["has_engine_constraint"] is True
        assert "node" in rules[0].stats["engines"]


class TestPythonDependencyHealth:
    """Tests for Python dependency health."""

    def test_detects_pinned_requirements(self, tmp_path: Path):
        """Detects exact pinning in requirements.txt."""
        from conventions.detectors.python.dependency_management import (
            PythonDependencyManagementDetector,
        )

        (tmp_path / "requirements.txt").write_text(
            "flask==3.0.0\n"
            "sqlalchemy==2.0.23\n"
            "pydantic==2.5.0\n"
            "requests>=2.28.0\n"
        )

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"python"},
            max_files=100,
        )
        result = PythonDependencyManagementDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "python.conventions.dependency_health"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["pinning_strategy"] == "exact"
        assert rule.stats["exact_count"] == 3
        assert rule.stats["minimum_count"] == 1
        assert rule.stats["total_deps"] == 4

    def test_detects_unpinned_requirements(self, tmp_path: Path):
        """Detects unpinned deps in requirements.txt."""
        from conventions.detectors.python.dependency_management import (
            PythonDependencyManagementDetector,
        )

        (tmp_path / "requirements.txt").write_text(
            "flask\n"
            "sqlalchemy\n"
            "pydantic\n"
        )

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"python"},
            max_files=100,
        )
        result = PythonDependencyManagementDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "python.conventions.dependency_health"]
        assert len(rules) == 1
        assert rules[0].stats["pinning_strategy"] == "unpinned"
        assert rules[0].stats["unpinned_count"] == 3

    def test_no_health_on_empty_repo(self, tmp_path: Path):
        """No dependency health rule on empty repo."""
        from conventions.detectors.python.dependency_management import (
            PythonDependencyManagementDetector,
        )

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"python"},
            max_files=100,
        )
        result = PythonDependencyManagementDetector().detect(ctx)
        assert not any(r.id.endswith("dependency_health") for r in result.rules)
