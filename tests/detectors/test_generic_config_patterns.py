"""Tests for config patterns detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext
from conventions.detectors.generic.config_patterns import ConfigPatternsDetector


@pytest.fixture
def node_env_repo(tmp_path: Path) -> Path:
    """Create a repo with process.env access and dotenv."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "config.ts").write_text(
        'import dotenv from "dotenv";\n'
        "dotenv.config();\n"
        "\n"
        "export const config = {\n"
        "  port: process.env.PORT || 3000,\n"
        "  dbUrl: process.env.DATABASE_URL,\n"
        "  secret: process.env.JWT_SECRET,\n"
        "};\n"
    )
    (src / "app.ts").write_text(
        'import { config } from "./config";\n'
        "const host = process.env.HOST || 'localhost';\n"
    )
    return tmp_path


@pytest.fixture
def python_settings_repo(tmp_path: Path) -> Path:
    """Create a repo with pydantic settings."""
    app = tmp_path / "app"
    app.mkdir()
    (app / "__init__.py").write_text("")
    (app / "settings.py").write_text(
        "from pydantic_settings import BaseSettings\n"
        "\n"
        "class Settings(BaseSettings):\n"
        '    db_url: str = "sqlite:///db.sqlite3"\n'
        '    secret_key: str = "changeme"\n'
        "    debug: bool = False\n"
    )
    (app / "main.py").write_text(
        "import os\n"
        'host = os.environ.get("HOST", "0.0.0.0")\n'
        'port = int(os.getenv("PORT", "8000"))\n'
    )
    return tmp_path


@pytest.fixture
def config_files_repo(tmp_path: Path) -> Path:
    """Create a repo with config files and directories."""
    (tmp_path / "config.yaml").write_text("app:\n  port: 3000\n")
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "default.json").write_text('{"port": 3000}')
    return tmp_path


@pytest.fixture
def secrets_repo(tmp_path: Path) -> Path:
    """Create a repo using secrets manager."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "secrets.py").write_text(
        "import boto3\n"
        "\n"
        "client = boto3.client('secretsmanager')\n"
        "response = client.GetSecretValue(SecretId='my-secret')\n"
    )
    (src / "config.py").write_text(
        "import os\n"
        'db = os.environ.get("DB_URL")\n'
        'key = os.getenv("API_KEY")\n'
    )
    return tmp_path


class TestConfigPatternsDetector:
    """Tests for ConfigPatternsDetector."""

    def test_detects_node_env_access(self, node_env_repo: Path):
        """Detects process.env access and dotenv library."""
        ctx = DetectorContext(repo_root=node_env_repo, selected_languages=set(), max_files=100)
        result = ConfigPatternsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.config_access"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["env_access_counts"]["node_process_env"] >= 4
        assert "node_dotenv" in rule.stats["libraries"]

    def test_detects_python_settings(self, python_settings_repo: Path):
        """Detects pydantic settings and os.environ access."""
        ctx = DetectorContext(repo_root=python_settings_repo, selected_languages=set(), max_files=100)
        result = ConfigPatternsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.config_access"]
        assert len(rules) == 1
        rule = rules[0]
        assert "pydantic_settings" in rule.stats["libraries"]
        assert rule.stats["env_access_counts"]["python_os_environ"] >= 2

    def test_detects_config_files(self, config_files_repo: Path):
        """Detects config files and directories."""
        ctx = DetectorContext(repo_root=config_files_repo, selected_languages=set(), max_files=100)
        result = ConfigPatternsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.config_files"]
        assert len(rules) == 1
        rule = rules[0]
        assert "config.yaml" in rule.stats["config_files"]
        assert "config" in rule.stats["config_dirs"]

    def test_detects_secrets_manager(self, secrets_repo: Path):
        """Detects secrets manager usage."""
        ctx = DetectorContext(repo_root=secrets_repo, selected_languages=set(), max_files=100)
        result = ConfigPatternsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.config_access"]
        assert len(rules) == 1
        rule = rules[0]
        assert "aws_secrets_manager" in rule.stats["secrets_managers"]

    def test_no_rules_on_empty_repo(self, tmp_path: Path):
        """No rules emitted when no config patterns found."""
        ctx = DetectorContext(repo_root=tmp_path, selected_languages=set(), max_files=100)
        result = ConfigPatternsDetector().detect(ctx)
        assert len(result.rules) == 0
