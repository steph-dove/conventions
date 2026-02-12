"""Tests for API route extraction across all languages."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext


@pytest.fixture
def node_api_repo(tmp_path: Path) -> Path:
    """Create a repo with Express-style routes."""
    routes = tmp_path / "src" / "routes"
    routes.mkdir(parents=True)
    (routes / "users.ts").write_text(
        'import { Router } from "express";\n'
        'const router = Router();\n'
        'router.get("/api/users", listUsers);\n'
        'router.post("/api/users", createUser);\n'
        'router.get("/api/users/:id", getUser);\n'
        'router.put("/api/users/:id", updateUser);\n'
        'router.delete("/api/users/:id", deleteUser);\n'
        'export default router;\n'
    )
    (routes / "health.ts").write_text(
        'import { Router } from "express";\n'
        'const router = Router();\n'
        'router.get("/health", healthCheck);\n'
        'export default router;\n'
    )
    return tmp_path


@pytest.fixture
def python_api_repo(tmp_path: Path) -> Path:
    """Create a repo with FastAPI-style routes."""
    src = tmp_path / "app"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "users.py").write_text(
        "from fastapi import APIRouter\n"
        "\n"
        "router = APIRouter()\n"
        "\n"
        '@router.get("/api/users")\n'
        "async def list_users():\n"
        "    pass\n"
        "\n"
        '@router.post("/api/users")\n'
        "async def create_user():\n"
        "    pass\n"
        "\n"
        '@router.get("/api/users/{user_id}")\n'
        "async def get_user(user_id: int):\n"
        "    pass\n"
        "\n"
        '@router.delete("/api/users/{user_id}")\n'
        "async def delete_user(user_id: int):\n"
        "    pass\n"
    )
    (src / "health.py").write_text(
        "from fastapi import APIRouter\n"
        "\n"
        "router = APIRouter()\n"
        "\n"
        '@router.get("/health")\n'
        "async def health():\n"
        "    pass\n"
    )
    return tmp_path


@pytest.fixture
def go_api_repo(tmp_path: Path) -> Path:
    """Create a repo with Gin-style routes."""
    handlers = tmp_path / "handlers"
    handlers.mkdir()
    (tmp_path / "go.mod").write_text("module github.com/example/app\n\ngo 1.21\n")
    (handlers / "users.go").write_text(
        "package handlers\n"
        "\n"
        'import "github.com/gin-gonic/gin"\n'
        "\n"
        "func RegisterRoutes(r *gin.Engine) {\n"
        '\tr.GET("/api/users", ListUsers)\n'
        '\tr.POST("/api/users", CreateUser)\n'
        '\tr.GET("/api/users/:id", GetUser)\n'
        '\tr.PUT("/api/users/:id", UpdateUser)\n'
        '\tr.DELETE("/api/users/:id", DeleteUser)\n'
        "}\n"
    )
    (handlers / "health.go").write_text(
        "package handlers\n"
        "\n"
        'import "github.com/gin-gonic/gin"\n'
        "\n"
        "func RegisterHealth(r *gin.Engine) {\n"
        '\tr.GET("/health", HealthCheck)\n'
        "}\n"
    )
    return tmp_path


@pytest.fixture
def rust_actix_repo(tmp_path: Path) -> Path:
    """Create a repo with Actix-web routes."""
    src = tmp_path / "src"
    src.mkdir()
    (tmp_path / "Cargo.toml").write_text(
        "[package]\n"
        'name = "myapp"\n'
        'version = "0.1.0"\n'
    )
    (src / "main.rs").write_text(
        "use actix_web::{get, post, put, delete, web, HttpResponse};\n"
        "\n"
        '#[get("/api/users")]\n'
        "async fn list_users() -> HttpResponse {\n"
        "    HttpResponse::Ok().finish()\n"
        "}\n"
        "\n"
        '#[post("/api/users")]\n'
        "async fn create_user() -> HttpResponse {\n"
        "    HttpResponse::Ok().finish()\n"
        "}\n"
        "\n"
        '#[get("/api/users/{id}")]\n'
        "async fn get_user() -> HttpResponse {\n"
        "    HttpResponse::Ok().finish()\n"
        "}\n"
        "\n"
        '#[delete("/api/users/{id}")]\n'
        "async fn delete_user() -> HttpResponse {\n"
        "    HttpResponse::Ok().finish()\n"
        "}\n"
        "\n"
        '#[get("/health")]\n'
        "async fn health() -> HttpResponse {\n"
        "    HttpResponse::Ok().finish()\n"
        "}\n"
    )
    return tmp_path


class TestNodeAPIRoutes:
    """Tests for Node.js API route extraction."""

    def test_detects_express_routes(self, node_api_repo: Path):
        """Detects Express-style route definitions."""
        from conventions.detectors.node.api import NodeAPIDetector

        ctx = DetectorContext(
            repo_root=node_api_repo,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeAPIDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.api_routes"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["total_routes"] == 6

        methods = rule.stats["methods"]
        assert methods["GET"] == 3
        assert methods["POST"] == 1
        assert methods["PUT"] == 1
        assert methods["DELETE"] == 1

        paths = [r["path"] for r in rule.stats["routes"]]
        assert "/api/users" in paths
        assert "/api/users/:id" in paths
        assert "/health" in paths

    def test_detects_path_prefixes(self, node_api_repo: Path):
        """Extracts common path prefixes from routes."""
        from conventions.detectors.node.api import NodeAPIDetector

        ctx = DetectorContext(
            repo_root=node_api_repo,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeAPIDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.api_routes"]
        assert len(rules) == 1
        assert "/api/users" in rules[0].stats["path_prefixes"]


class TestPythonAPIRoutes:
    """Tests for Python API route extraction."""

    def test_detects_fastapi_routes(self, python_api_repo: Path):
        """Detects FastAPI-style route definitions."""
        from conventions.detectors.python.api_response_patterns import (
            PythonAPIResponsePatternsDetector,
        )

        ctx = DetectorContext(
            repo_root=python_api_repo,
            selected_languages={"python"},
            max_files=100,
        )
        result = PythonAPIResponsePatternsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "python.conventions.api_routes"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["total_routes"] == 5

        methods = rule.stats["methods"]
        assert methods["GET"] == 3
        assert methods["POST"] == 1
        assert methods["DELETE"] == 1

        paths = [r["path"] for r in rule.stats["routes"]]
        assert "/api/users" in paths
        assert "/health" in paths


class TestGoAPIRoutes:
    """Tests for Go API route extraction."""

    def test_detects_gin_routes(self, go_api_repo: Path):
        """Detects Gin-style route definitions."""
        from conventions.detectors.go.api import GoAPIDetector

        ctx = DetectorContext(
            repo_root=go_api_repo,
            selected_languages={"go"},
            max_files=100,
        )
        result = GoAPIDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "go.conventions.api_routes"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["total_routes"] == 6

        methods = rule.stats["methods"]
        assert methods["GET"] == 3
        assert methods["POST"] == 1
        assert methods["PUT"] == 1
        assert methods["DELETE"] == 1

        paths = [r["path"] for r in rule.stats["routes"]]
        assert "/api/users" in paths
        assert "/api/users/:id" in paths
        assert "/health" in paths

    def test_detects_path_prefixes(self, go_api_repo: Path):
        """Extracts common path prefixes."""
        from conventions.detectors.go.api import GoAPIDetector

        ctx = DetectorContext(
            repo_root=go_api_repo,
            selected_languages={"go"},
            max_files=100,
        )
        result = GoAPIDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "go.conventions.api_routes"]
        assert "/api/users" in rules[0].stats["path_prefixes"]


class TestRustAPIRoutes:
    """Tests for Rust API route extraction."""

    def test_detects_actix_routes(self, rust_actix_repo: Path):
        """Detects Actix-web attribute macro routes."""
        from conventions.detectors.rust.web import RustWebDetector

        ctx = DetectorContext(
            repo_root=rust_actix_repo,
            selected_languages={"rust"},
            max_files=100,
        )
        result = RustWebDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "rust.conventions.api_routes"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["total_routes"] == 5

        methods = rule.stats["methods"]
        assert methods["GET"] == 3
        assert methods["POST"] == 1
        assert methods["DELETE"] == 1

        paths = [r["path"] for r in rule.stats["routes"]]
        assert "/api/users" in paths
        assert "/api/users/{id}" in paths
        assert "/health" in paths


class TestNoRoutesEmptyRepo:
    """Tests that no routes are emitted on empty repos."""

    def test_node_empty(self, tmp_path: Path):
        """No routes on empty Node repo."""
        from conventions.detectors.node.api import NodeAPIDetector

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeAPIDetector().detect(ctx)
        assert not any(r.id.endswith("api_routes") for r in result.rules)

    def test_go_empty(self, tmp_path: Path):
        """No routes on empty Go repo."""
        from conventions.detectors.go.api import GoAPIDetector

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"go"},
            max_files=100,
        )
        result = GoAPIDetector().detect(ctx)
        assert not any(r.id.endswith("api_routes") for r in result.rules)
