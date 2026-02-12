"""Tests for monorepo package listing."""
from __future__ import annotations

import json
from pathlib import Path

from conventions.detectors.base import DetectorContext
from conventions.detectors.node.monorepo import NodeMonorepoDetector


class TestMonorepoPackages:
    """Tests for monorepo package name detection."""

    def test_detect_package_names(self, tmp_path: Path):
        """Detects individual package names from packages/."""
        (tmp_path / "package.json").write_text(json.dumps({
            "name": "root",
            "workspaces": ["packages/*"],
        }))
        (tmp_path / "turbo.json").write_text("{}")

        packages = tmp_path / "packages"
        packages.mkdir()

        api = packages / "api"
        api.mkdir()
        (api / "package.json").write_text(json.dumps({"name": "@org/api"}))

        shared = packages / "shared"
        shared.mkdir()
        (shared / "package.json").write_text(json.dumps({"name": "@org/shared", "private": True}))

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeMonorepoDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.monorepo"]
        assert len(rules) == 1
        pkgs = rules[0].stats["packages"]
        assert len(pkgs) == 2
        names = [p["name"] for p in pkgs]
        assert "@org/api" in names
        assert "@org/shared" in names

    def test_detect_apps_and_packages(self, tmp_path: Path):
        """Detects packages from both packages/ and apps/ dirs."""
        (tmp_path / "package.json").write_text(json.dumps({
            "name": "root",
            "workspaces": ["packages/*", "apps/*"],
        }))
        (tmp_path / "turbo.json").write_text("{}")

        for dir_name, pkg_name in [("packages/lib", "@org/lib"), ("apps/web", "@org/web")]:
            d = tmp_path / dir_name
            d.mkdir(parents=True)
            (d / "package.json").write_text(json.dumps({"name": pkg_name}))

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeMonorepoDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.monorepo"]
        assert len(rules) == 1
        pkgs = rules[0].stats["packages"]
        assert len(pkgs) == 2

    def test_empty_monorepo(self, tmp_path: Path):
        """Monorepo with no packages still detects tools."""
        (tmp_path / "package.json").write_text(json.dumps({
            "name": "root",
            "workspaces": ["packages/*"],
        }))
        (tmp_path / "turbo.json").write_text("{}")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeMonorepoDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.monorepo"]
        assert len(rules) == 1
        assert rules[0].stats["packages"] == []
        assert rules[0].stats["package_count"] == 0
