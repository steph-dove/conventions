"""Rust database conventions detector."""

from __future__ import annotations

import re

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import RustDetector
from .index import make_evidence


@DetectorRegistry.register
class RustDatabaseDetector(RustDetector):
    """Detect Rust database conventions."""

    name = "rust_database"
    description = "Detects database libraries and ORM patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect database conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        libraries: dict[str, dict] = {}
        examples: list[tuple[str, int]] = []

        # Check for Diesel
        diesel_uses = index.find_uses_matching("diesel", limit=50)
        if diesel_uses:
            libraries["diesel"] = {
                "name": "Diesel",
                "type": "ORM",
                "count": len(diesel_uses),
            }
            examples.extend([(r, ln) for r, _, ln in diesel_uses[:3]])

        # Check for SQLx
        sqlx_uses = index.find_uses_matching("sqlx", limit=50)
        if sqlx_uses:
            libraries["sqlx"] = {
                "name": "SQLx",
                "type": "async SQL",
                "count": len(sqlx_uses),
            }
            examples.extend([(r, ln) for r, _, ln in sqlx_uses[:3]])

        # Check for SeaORM
        sea_orm_uses = index.find_uses_matching("sea_orm", limit=50)
        if sea_orm_uses:
            libraries["sea_orm"] = {
                "name": "SeaORM",
                "type": "async ORM",
                "count": len(sea_orm_uses),
            }
            examples.extend([(r, ln) for r, _, ln in sea_orm_uses[:3]])

        # Check for rusqlite
        rusqlite_uses = index.find_uses_matching("rusqlite", limit=30)
        if rusqlite_uses:
            libraries["rusqlite"] = {
                "name": "rusqlite",
                "type": "SQLite",
                "count": len(rusqlite_uses),
            }

        # Check for tokio-postgres
        tokio_pg_uses = index.find_uses_matching("tokio_postgres", limit=30)
        if tokio_pg_uses:
            libraries["tokio_postgres"] = {
                "name": "tokio-postgres",
                "type": "async PostgreSQL",
                "count": len(tokio_pg_uses),
            }

        # Check for postgres
        postgres_uses = index.find_uses_matching("postgres", limit=30)
        postgres_uses = [u for u in postgres_uses if "tokio_postgres" not in u[1]]
        if postgres_uses:
            libraries["postgres"] = {
                "name": "postgres",
                "type": "PostgreSQL",
                "count": len(postgres_uses),
            }

        # Check for mongodb
        mongodb_uses = index.find_uses_matching("mongodb", limit=30)
        if mongodb_uses:
            libraries["mongodb"] = {
                "name": "MongoDB",
                "type": "NoSQL",
                "count": len(mongodb_uses),
            }

        # Check for redis
        redis_uses = index.find_uses_matching("redis", limit=30)
        if redis_uses:
            libraries["redis"] = {
                "name": "Redis",
                "type": "key-value",
                "count": len(redis_uses),
            }

        # Check for sled
        sled_uses = index.find_uses_matching("sled", limit=30)
        if sled_uses:
            libraries["sled"] = {
                "name": "sled",
                "type": "embedded",
                "count": len(sled_uses),
            }

        # Check for migrations
        migrations = []

        # diesel migrations
        diesel_migrations = ctx.repo_root / "migrations"
        if diesel_migrations.is_dir():
            sql_files = list(diesel_migrations.glob("**/up.sql"))
            if sql_files:
                migrations.append(("diesel", len(sql_files)))

        # sqlx migrations
        sqlx_migrations = ctx.repo_root / "migrations"
        if sqlx_migrations.is_dir():
            sqlx_files = list(sqlx_migrations.glob("**/*.sql"))
            if sqlx_files and "diesel" not in libraries:
                migrations.append(("sqlx", len(sqlx_files)))

        # refinery migrations
        refinery_uses = index.find_uses_matching("refinery", limit=10)
        if refinery_uses:
            migrations.append(("refinery", len(refinery_uses)))

        if not libraries:
            return result

        # Determine primary
        priority = ["sqlx", "diesel", "sea_orm", "tokio_postgres", "postgres", "mongodb", "redis", "rusqlite", "sled"]
        primary = None
        for lib in priority:
            if lib in libraries:
                primary = lib
                break
        if primary is None:
            primary = list(libraries.keys())[0]

        lib_info = libraries[primary]
        title = f"Database: {lib_info['name']}"
        description = f"Uses {lib_info['name']} ({lib_info['type']})."

        if len(libraries) > 1:
            others = [lib["name"] for k, lib in libraries.items() if k != primary]
            description += f" Also: {', '.join(others[:3])}."

        if migrations:
            mig_tool, mig_count = migrations[0]
            description += f" {mig_count} migration(s)."

        confidence = 0.95

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.database",
            category="database",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "libraries": list(libraries.keys()),
                "primary_library": primary,
                "migrations": migrations,
                "library_details": libraries,
            },
        ))

        # Detect database entities
        self._detect_entities(ctx, index, result)

        return result

    def _detect_entities(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect database entities from Rust derive macros and struct patterns."""
        entities: list[dict[str, str]] = []
        orm = None

        # Patterns that indicate a DB entity struct
        db_derives = re.compile(
            r"#\[derive\([^)]*(?:FromRow|Queryable|Insertable|AsChangeset|"
            r"DeriveEntityModel|DeriveActiveModel)[^)]*\)\]"
        )
        diesel_table = re.compile(r"table!\s*\{")

        for rel_path, file_idx in index.files.items():
            if file_idx.role == "test":
                continue

            content = "\n".join(file_idx.lines)

            for struct_name, struct_line, _is_pub in file_idx.structs:
                # Check lines before the struct for derive macros
                start = max(0, struct_line - 5)
                end = struct_line
                block = "\n".join(file_idx.lines[start:end])

                if db_derives.search(block):
                    entities.append({"name": struct_name, "file": rel_path})
                    if "DeriveEntityModel" in block or "DeriveActiveModel" in block:
                        orm = orm or "sea_orm"
                    elif "Queryable" in block or "Insertable" in block:
                        orm = orm or "diesel"
                    else:
                        orm = orm or "sqlx"

            # Also check for Diesel table! macros
            if diesel_table.search(content):
                orm = orm or "diesel"

        if not entities:
            return

        names = [e["name"] for e in entities[:10]]
        description = (
            f"{len(entities)} {orm or 'DB'} entities: {', '.join(names)}"
            + ("..." if len(entities) > 10 else "") + "."
        )

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.db_entities",
            category="database",
            title="Database entities",
            description=description,
            confidence=0.90,
            language="rust",
            evidence=[],
            stats={
                "entities": entities,
                "entity_count": len(entities),
                "orm": orm or "unknown",
            },
        ))
