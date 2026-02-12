"""Tests for Node.js migrations detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext
from conventions.detectors.node.migrations import NodeMigrationsDetector


@pytest.fixture
def prisma_repo(tmp_path: Path) -> Path:
    """Create a repo with Prisma setup."""
    prisma = tmp_path / "prisma"
    prisma.mkdir()
    (prisma / "schema.prisma").write_text(
        "generator client {\n"
        '  provider = "prisma-client-js"\n'
        "}\n"
        "\n"
        "datasource db {\n"
        '  provider = "postgresql"\n'
        '  url = env("DATABASE_URL")\n'
        "}\n"
        "\n"
        "model User {\n"
        "  id    Int    @id @default(autoincrement())\n"
        "  email String @unique\n"
        "}\n"
    )
    migrations = prisma / "migrations"
    migrations.mkdir()
    (migrations / "20240101_init").mkdir()
    (migrations / "20240102_add_users").mkdir()

    src = tmp_path / "src"
    src.mkdir()
    (src / "db.ts").write_text(
        'import { PrismaClient } from "@prisma/client";\n'
        "export const prisma = new PrismaClient();\n"
    )
    return tmp_path


@pytest.fixture
def knex_repo(tmp_path: Path) -> Path:
    """Create a repo with Knex setup."""
    (tmp_path / "knexfile.js").write_text(
        "module.exports = {\n"
        "  client: 'postgresql',\n"
        "  connection: process.env.DATABASE_URL,\n"
        "};\n"
    )
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_create_users.js").write_text("exports.up = () => {};\n")
    (migrations / "002_add_posts.js").write_text("exports.up = () => {};\n")
    (migrations / "003_add_comments.js").write_text("exports.up = () => {};\n")

    src = tmp_path / "src"
    src.mkdir()
    (src / "db.ts").write_text(
        'import knex from "knex";\n'
        "export const db = knex(config);\n"
    )
    return tmp_path


@pytest.fixture
def drizzle_repo(tmp_path: Path) -> Path:
    """Create a repo with Drizzle setup via package.json."""
    (tmp_path / "drizzle.config.ts").write_text(
        'import { defineConfig } from "drizzle-kit";\n'
        "export default defineConfig({});\n"
    )
    drizzle = tmp_path / "drizzle"
    drizzle.mkdir()
    (drizzle / "0001_init.sql").write_text("CREATE TABLE users;\n")
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"drizzle-orm": "^0.30.0"}}\n'
    )
    return tmp_path


class TestNodeMigrationsDetector:
    """Tests for NodeMigrationsDetector."""

    def test_detects_prisma(self, prisma_repo: Path):
        """Detects Prisma schema and migrations."""
        ctx = DetectorContext(
            repo_root=prisma_repo,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeMigrationsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.db_migrations"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["primary_tool"] == "prisma"
        tools = rule.stats["tools"]
        prisma = next(t for t in tools if t["name"] == "prisma")
        assert prisma["has_config"] is True
        assert prisma["has_import"] is True
        assert prisma["migration_count"] == 2

    def test_detects_knex(self, knex_repo: Path):
        """Detects Knex config and migrations."""
        ctx = DetectorContext(
            repo_root=knex_repo,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeMigrationsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.db_migrations"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["primary_tool"] == "knex"
        assert rule.stats["total_migration_files"] == 3

    def test_detects_drizzle_from_package_json(self, drizzle_repo: Path):
        """Detects Drizzle via package.json dependency."""
        ctx = DetectorContext(
            repo_root=drizzle_repo,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeMigrationsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "node.conventions.db_migrations"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["primary_tool"] == "drizzle"

    def test_no_rules_on_empty_repo(self, tmp_path: Path):
        """No rules emitted when no migration tools found."""
        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        result = NodeMigrationsDetector().detect(ctx)
        assert len(result.rules) == 0
