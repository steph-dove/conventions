"""Tests for Node.js frontend framework detection."""
from __future__ import annotations

import json
from pathlib import Path

from conventions.detectors.base import DetectorContext


class TestNodeFrontendMonorepo:
    """Tests for monorepo-aware frontend detection."""

    def test_detect_react_in_workspace_package(self, tmp_path: Path):
        """Detects React from workspace package.json, not just root."""
        from conventions.detectors.node.frontend import NodeFrontendDetector

        # Root package.json with workspaces but no react
        (tmp_path / "package.json").write_text(json.dumps({
            "name": "my-monorepo",
            "workspaces": ["src/*", "server-ts"],
        }))

        # Client workspace with react
        client_dir = tmp_path / "src" / "client"
        client_dir.mkdir(parents=True)
        (client_dir / "package.json").write_text(json.dumps({
            "name": "@myorg/client",
            "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"},
        }))
        (client_dir / "App.tsx").write_text(
            "import React from 'react';\n"
            "export const App = () => <div>Hello</div>;\n"
        )

        # Server workspace without react
        server_dir = tmp_path / "server-ts"
        server_dir.mkdir()
        (server_dir / "package.json").write_text(json.dumps({
            "name": "@myorg/server",
            "dependencies": {"express": "^4.0.0"},
        }))
        (server_dir / "index.ts").write_text("import express from 'express';\n")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeFrontendDetector().detect(ctx)

        frontend_rules = [r for r in result.rules if r.id == "node.conventions.frontend"]
        assert len(frontend_rules) == 1
        assert frontend_rules[0].stats["primary_framework"] == "react"

    def test_detect_react_from_root_package(self, tmp_path: Path):
        """Still detects React from root package.json (non-monorepo)."""
        from conventions.detectors.node.frontend import NodeFrontendDetector

        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"},
        }))
        (tmp_path / "App.tsx").write_text(
            "import React from 'react';\n"
            "export const App = () => <div>Hello</div>;\n"
        )

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeFrontendDetector().detect(ctx)

        frontend_rules = [r for r in result.rules if r.id == "node.conventions.frontend"]
        assert len(frontend_rules) == 1
        assert frontend_rules[0].stats["primary_framework"] == "react"

    def test_no_false_positive_without_framework(self, tmp_path: Path):
        """No frontend detected when no framework is present."""
        from conventions.detectors.node.frontend import NodeFrontendDetector

        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {"express": "^4.0.0"},
        }))
        (tmp_path / "index.ts").write_text("import express from 'express';\n")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeFrontendDetector().detect(ctx)

        frontend_rules = [r for r in result.rules if r.id == "node.conventions.frontend"]
        assert len(frontend_rules) == 0
