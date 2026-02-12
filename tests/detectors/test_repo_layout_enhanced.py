"""Tests for enhanced repo layout detection."""
from __future__ import annotations

import json
from pathlib import Path

from conventions.detectors.base import DetectorContext
from conventions.detectors.generic.repo_layout import GenericRepoLayoutDetector


class TestEnhancedRepoLayout:
    """Tests for recursive directory tree detection."""

    def test_detect_top_level_dirs(self, tmp_path: Path):
        """Detects top-level directories with purpose annotations."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_app.py").write_text("")
        (tmp_path / "docs").mkdir()

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages=set(),
            max_files=100,
        )
        result = GenericRepoLayoutDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.repo_layout"]
        assert len(rules) == 1
        tree = rules[0].stats["directory_tree"]
        assert "src" in tree
        assert tree["src"]["purpose"] == "source code"
        assert "tests" in tree
        assert "docs" in tree

    def test_recursive_subdirectories(self, tmp_path: Path):
        """Recursively lists subdirectories within main directories."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "routes").mkdir()
        (src / "services").mkdir()
        (src / "models").mkdir()
        (src / "routes" / "api").mkdir()

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages=set(),
            max_files=100,
        )
        result = GenericRepoLayoutDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.repo_layout"]
        assert len(rules) == 1
        tree = rules[0].stats["directory_tree"]
        children = tree["src"]["children"]
        assert "routes" in children
        assert "services" in children
        assert "models" in children
        # Depth 2: routes/api
        assert "api" in children["routes"]["children"]

    def test_skips_noise_dirs(self, tmp_path: Path):
        """Skips node_modules, .git, dist, etc."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.ts").write_text("")
        (src / "node_modules").mkdir()
        (src / "dist").mkdir()
        (src / "routes").mkdir()

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages=set(),
            max_files=100,
        )
        result = GenericRepoLayoutDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.repo_layout"]
        tree = rules[0].stats["directory_tree"]
        children = tree["src"]["children"]
        assert "routes" in children
        assert "node_modules" not in children
        assert "dist" not in children

    def test_workspace_dirs_with_descriptions(self, tmp_path: Path):
        """Workspace directories get descriptions from their package.json."""
        (tmp_path / "package.json").write_text(json.dumps({
            "workspaces": ["src/*", "server-ts"],
        }))
        # server-ts workspace
        ws = tmp_path / "server-ts"
        ws.mkdir()
        (ws / "package.json").write_text(json.dumps({
            "name": "@myorg/server",
            "description": "REST API server",
        }))
        ws_src = ws / "src"
        ws_src.mkdir()
        (ws_src / "routes").mkdir()
        (ws_src / "services").mkdir()
        # src workspace children
        (tmp_path / "src").mkdir()
        client = tmp_path / "src" / "client"
        client.mkdir()
        (client / "package.json").write_text(json.dumps({
            "name": "@myorg/client",
            "description": "React frontend",
        }))
        (client / "components").mkdir()

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages=set(),
            max_files=100,
        )
        result = GenericRepoLayoutDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.repo_layout"]
        assert len(rules) == 1
        tree = rules[0].stats["directory_tree"]
        # server-ts is a top-level workspace
        assert "server-ts" in tree
        assert tree["server-ts"]["purpose"] == "REST API server"
        assert "src" in tree["server-ts"]["children"]
        assert "routes" in tree["server-ts"]["children"]["src"]["children"]
        # src/client is a workspace child with description
        src_children = tree["src"]["children"]
        assert "client" in src_children
        assert src_children["client"]["purpose"] == "React frontend"
        assert "components" in src_children["client"]["children"]

    def test_project_description_from_package_json(self, tmp_path: Path):
        """Extracts project description from package.json."""
        (tmp_path / "package.json").write_text(json.dumps({
            "name": "my-app",
            "description": "Property management application",
        }))
        (tmp_path / "src").mkdir()

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages=set(),
            max_files=100,
        )
        result = GenericRepoLayoutDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.repo_layout"]
        assert len(rules) == 1
        assert rules[0].stats["project_description"] == "Property management application"

    def test_project_description_from_pyproject(self, tmp_path: Path):
        """Extracts project description from pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "mylib"\ndescription = "A library for data processing"\n'
        )
        (tmp_path / "src").mkdir()

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages=set(),
            max_files=100,
        )
        result = GenericRepoLayoutDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.repo_layout"]
        assert len(rules) == 1
        assert rules[0].stats["project_description"] == "A library for data processing"

    def test_depth_limit(self, tmp_path: Path):
        """Recursion stops at max_depth (3 levels from root)."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a").mkdir()
        (tmp_path / "src" / "a" / "b").mkdir()
        (tmp_path / "src" / "a" / "b" / "c").mkdir()  # depth 4 — should not appear

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages=set(),
            max_files=100,
        )
        result = GenericRepoLayoutDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.repo_layout"]
        tree = rules[0].stats["directory_tree"]
        # src (depth 1) -> a (depth 2) -> b (depth 3) should exist
        assert "b" in tree["src"]["children"]["a"]["children"]
        # b -> c (depth 4) should be empty
        assert tree["src"]["children"]["a"]["children"]["b"]["children"] == {}
