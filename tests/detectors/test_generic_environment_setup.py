"""Tests for environment setup detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext
from conventions.detectors.generic.environment_setup import EnvironmentSetupDetector


@pytest.fixture
def env_example_repo(tmp_path: Path) -> Path:
    """Create a repo with .env.example."""
    (tmp_path / ".env.example").write_text(
        "# Database\n"
        "DATABASE_URL=\n"
        "DB_HOST=localhost\n"
        "\n"
        "# Auth\n"
        "JWT_SECRET=\n"
        "API_KEY=\n"
        "\n"
        "# App\n"
        "PORT=3000\n"
        "NODE_ENV=development\n"
        "\n"
        "# Services\n"
        "REDIS_URL=\n"
    )
    return tmp_path


@pytest.fixture
def docker_compose_repo(tmp_path: Path) -> Path:
    """Create a repo with docker-compose.yml."""
    (tmp_path / "docker-compose.yml").write_text(
        "version: '3.8'\n"
        "\n"
        "services:\n"
        "  postgres:\n"
        "    image: postgres:15\n"
        "    ports:\n"
        "      - '5432:5432'\n"
        "    environment:\n"
        "      POSTGRES_DB: myapp\n"
        "  redis:\n"
        "    image: redis:7-alpine\n"
        "    ports:\n"
        "      - '6379:6379'\n"
        "  app:\n"
        "    build: .\n"
        "    ports:\n"
        "      - '3000:3000'\n"
    )
    return tmp_path


@pytest.fixture
def prerequisites_repo(tmp_path: Path) -> Path:
    """Create a repo with runtime version files."""
    (tmp_path / ".node-version").write_text("20.10.0\n")
    (tmp_path / ".python-version").write_text("3.11.5\n")
    return tmp_path


class TestEnvironmentSetupDetector:
    """Tests for EnvironmentSetupDetector."""

    def test_detects_env_example(self, env_example_repo: Path):
        """Detects and categorizes .env.example variables."""
        ctx = DetectorContext(repo_root=env_example_repo, selected_languages=set(), max_files=100)
        result = EnvironmentSetupDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.env_setup"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["total_vars"] == 7
        assert rule.stats["env_file"] == ".env.example"

        categories = rule.stats["var_categories"]
        assert categories["database"] >= 2
        assert categories["auth"] >= 2
        assert categories["app"] >= 2
        assert categories["service"] >= 1

    def test_env_vars_have_defaults(self, env_example_repo: Path):
        """Detects which env vars have default values."""
        ctx = DetectorContext(repo_root=env_example_repo, selected_languages=set(), max_files=100)
        result = EnvironmentSetupDetector().detect(ctx)

        vars = result.rules[0].stats["env_vars"]
        port = next(v for v in vars if v["name"] == "PORT")
        assert port["has_default"] is True
        assert port["default"] == "3000"

        jwt = next(v for v in vars if v["name"] == "JWT_SECRET")
        assert jwt["has_default"] is False

    def test_detects_docker_compose_services(self, docker_compose_repo: Path):
        """Detects services from docker-compose.yml."""
        ctx = DetectorContext(repo_root=docker_compose_repo, selected_languages=set(), max_files=100)
        result = EnvironmentSetupDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.required_services"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["total_services"] >= 2

        services = rule.stats["services"]
        names = [s["name"] for s in services]
        assert "postgres" in names
        assert "redis" in names

        pg = next(s for s in services if s["name"] == "postgres")
        assert pg["image"] == "postgres:15"

    def test_detects_prerequisites(self, prerequisites_repo: Path):
        """Detects runtime version prerequisites."""
        ctx = DetectorContext(repo_root=prerequisites_repo, selected_languages=set(), max_files=100)
        result = EnvironmentSetupDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.runtime_prerequisites"]
        assert len(rules) == 1
        rule = rules[0]
        tools = rule.stats["tools"]
        names = [t["name"] for t in tools]
        assert "node" in names
        assert "python" in names

        node = next(t for t in tools if t["name"] == "node")
        assert node["version"] == "20.10.0"

    def test_detects_tool_versions(self, tmp_path: Path):
        """Detects tools from .tool-versions (asdf)."""
        (tmp_path / ".tool-versions").write_text(
            "nodejs 20.10.0\n"
            "python 3.11.5\n"
            "golang 1.21.0\n"
        )
        ctx = DetectorContext(repo_root=tmp_path, selected_languages=set(), max_files=100)
        result = EnvironmentSetupDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.runtime_prerequisites"]
        assert len(rules) == 1
        assert len(rules[0].stats["tools"]) == 3

    def test_no_rules_on_empty_repo(self, tmp_path: Path):
        """No rules emitted when no env setup files found."""
        ctx = DetectorContext(repo_root=tmp_path, selected_languages=set(), max_files=100)
        result = EnvironmentSetupDetector().detect(ctx)
        assert len(result.rules) == 0
