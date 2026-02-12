"""Tests for import path alias detection."""
from __future__ import annotations

import json
from pathlib import Path

from conventions.detectors.base import DetectorContext


class TestNodePathAliases:
    """Tests for TypeScript path alias detection."""

    def test_detect_tsconfig_paths(self, tmp_path: Path):
        """Detects path aliases from tsconfig.json."""
        from conventions.detectors.node.typescript import NodeTypeScriptDetector

        # Create a minimal TypeScript project
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "tsconfig.json").write_text(json.dumps({
            "compilerOptions": {
                "baseUrl": ".",
                "paths": {
                    "@/*": ["src/*"],
                    "@components/*": ["src/components/*"],
                },
            },
        }))
        # Need at least one TS file for the index
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.ts").write_text("export const x = 1;")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeTypeScriptDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.import_aliases"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["aliases"]["@/*"] == "src/*"
        assert rule.stats["aliases"]["@components/*"] == "src/components/*"
        assert rule.stats["base_url"] == "."

    def test_no_tsconfig(self, tmp_path: Path):
        """No aliases when tsconfig.json is missing."""
        from conventions.detectors.node.typescript import NodeTypeScriptDetector

        (tmp_path / "package.json").write_text('{"name": "test"}')
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.ts").write_text("export const x = 1;")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeTypeScriptDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.import_aliases"]
        assert len(rules) == 0


class TestGoModuleImportPath:
    """Tests for Go module import path detection."""

    def test_detect_module_path(self, tmp_path: Path):
        """Detects Go module import path from go.mod."""
        from conventions.detectors.go.modules import GoModulesDetector

        (tmp_path / "go.mod").write_text(
            "module github.com/myorg/myproject\n\ngo 1.22\n"
        )
        (tmp_path / "go.sum").write_text("")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"go"},
            max_files=100,
        )
        result = GoModulesDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "go.conventions.import_aliases"]
        assert len(rules) == 1
        assert rules[0].stats["module_path"] == "github.com/myorg/myproject"


class TestPythonSrcLayout:
    """Tests for Python src-layout detection."""

    def test_detect_src_layout(self, tmp_path: Path):
        """Detects src-layout with package."""
        from conventions.detectors.python.dependency_management import (
            PythonDependencyManagementDetector,
        )

        (tmp_path / "requirements.txt").write_text("flask==3.0.0\n")
        src = tmp_path / "src"
        src.mkdir()
        pkg = src / "mypackage"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"python"},
            max_files=100,
        )
        result = PythonDependencyManagementDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "python.conventions.import_aliases"]
        assert len(rules) == 1
        assert rules[0].stats["layout"] == "src"
        assert rules[0].stats["package_name"] == "mypackage"

    def test_detect_flat_layout(self, tmp_path: Path):
        """Detects flat layout with top-level package."""
        from conventions.detectors.python.dependency_management import (
            PythonDependencyManagementDetector,
        )

        (tmp_path / "requirements.txt").write_text("flask==3.0.0\n")
        pkg = tmp_path / "myapp"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"python"},
            max_files=100,
        )
        result = PythonDependencyManagementDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "python.conventions.import_aliases"]
        assert len(rules) == 1
        assert rules[0].stats["layout"] == "flat"
        assert rules[0].stats["package_name"] == "myapp"
