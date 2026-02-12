"""Python database conventions detector."""

from __future__ import annotations

import re
from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence

# Database library patterns
DB_LIBRARIES = {
    "sqlalchemy": {
        "imports": ["sqlalchemy"],
        "name": "SQLAlchemy",
    },
    "asyncpg": {
        "imports": ["asyncpg"],
        "name": "asyncpg",
    },
    "psycopg": {
        "imports": ["psycopg", "psycopg2"],
        "name": "psycopg/psycopg2",
    },
    "pymongo": {
        "imports": ["pymongo"],
        "name": "PyMongo",
    },
    "motor": {
        "imports": ["motor"],
        "name": "Motor (async MongoDB)",
    },
    "redis": {
        "imports": ["redis", "aioredis"],
        "name": "Redis",
    },
    "sqlite": {
        "imports": ["sqlite3", "aiosqlite"],
        "name": "SQLite",
    },
    "tortoise": {
        "imports": ["tortoise"],
        "name": "Tortoise ORM",
    },
    "sqlmodel": {
        "imports": ["sqlmodel"],
        "name": "SQLModel",
    },
    "peewee": {
        "imports": ["peewee"],
        "name": "Peewee",
    },
    "databases": {
        "imports": ["databases"],
        "name": "databases (async)",
    },
}


@DetectorRegistry.register
class PythonDBConventionsDetector(PythonDetector):
    """Detect Python database access conventions."""

    name = "python_db_conventions"
    description = "Detects database library usage, session patterns, and query styles"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect database library usage, session patterns, and query styles."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect primary DB library
        self._detect_db_library(ctx, index, result)

        # Detect session lifecycle patterns (SQLAlchemy specific)
        self._detect_session_lifecycle(ctx, index, result)

        # Detect query style (SQLAlchemy specific)
        self._detect_query_style(ctx, index, result)

        # Detect transaction patterns
        self._detect_transactions(ctx, index, result)

        # Detect migrations
        self._detect_migrations(ctx, index, result)

        # Detect connection pooling
        self._detect_connection_pooling(ctx, index, result)

        # Detect async ORM usage
        self._detect_async_orm(ctx, index, result)

        # Detect database entities
        self._detect_entities(ctx, index, result)

        return result

    def _detect_db_library(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect which database libraries are used."""
        library_counts: Counter[str] = Counter()
        library_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # Skip test and docs files
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            for lib_key, lib_info in DB_LIBRARIES.items():
                for pattern in lib_info["imports"]:
                    if pattern in imp.module or pattern in imp.names:
                        library_counts[lib_key] += 1
                        if lib_key not in library_examples:
                            library_examples[lib_key] = []
                        if len(library_examples[lib_key]) < 5:
                            library_examples[lib_key].append((rel_path, imp.line))
                        break

        if not library_counts:
            return

        # Find primary library
        primary_lib, primary_count = library_counts.most_common(1)[0]
        total_imports = sum(library_counts.values())
        primary_ratio = primary_count / total_imports if total_imports else 0

        # Build description
        lib_names: list[str] = [str(DB_LIBRARIES[lib]["name"]) for lib in library_counts.keys()]

        if len(library_counts) == 1:
            title = f"Single database library: {DB_LIBRARIES[primary_lib]['name']}"
            description = (
                f"Uses {DB_LIBRARIES[primary_lib]['name']} exclusively for database access. "
                f"Found {primary_count} imports."
            )
            confidence = min(0.95, 0.7 + primary_count * 0.02)
        else:
            title = f"Primary database library: {DB_LIBRARIES[primary_lib]['name']}"
            description = (
                f"Uses {DB_LIBRARIES[primary_lib]['name']} as primary database library "
                f"({primary_count}/{total_imports} imports). "
                f"Also uses: {', '.join(lib_names[1:])}."
            )
            confidence = min(0.85, 0.5 + primary_ratio * 0.35)

        # Build evidence
        evidence = []
        for rel_path, line in library_examples.get(primary_lib, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.db_library",
            category="database",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "library_counts": dict(library_counts),
                "primary_library": primary_lib,
                "primary_ratio": round(primary_ratio, 3),
            },
        ))

    def _detect_session_lifecycle(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect SQLAlchemy session lifecycle patterns."""
        # Check if SQLAlchemy is used
        sa_import_count = index.count_imports_matching("sqlalchemy")
        if sa_import_count < 2:
            return

        # Pattern counters
        patterns: Counter[str] = Counter()
        pattern_examples: dict[str, list[tuple[str, int]]] = {}

        # Check for sessionmaker/SessionLocal pattern
        for rel_path, call in index.get_all_calls():
            if "sessionmaker" in call.name:
                patterns["sessionmaker"] += 1
                if "sessionmaker" not in pattern_examples:
                    pattern_examples["sessionmaker"] = []
                pattern_examples["sessionmaker"].append((rel_path, call.line))

            if "SessionLocal" in call.name:
                patterns["SessionLocal"] += 1
                if "SessionLocal" not in pattern_examples:
                    pattern_examples["SessionLocal"] = []
                pattern_examples["SessionLocal"].append((rel_path, call.line))

        # Check for get_db dependency pattern
        for rel_path, func in index.get_all_functions():
            if func.name == "get_db":
                patterns["get_db"] += 1
                if "get_db" not in pattern_examples:
                    pattern_examples["get_db"] = []
                pattern_examples["get_db"].append((rel_path, func.line))

        # Check for Depends(get_db) pattern
        depends_get_db_count = 0
        for rel_path, call in index.get_all_calls():
            if call.name == "Depends" and len(call.kwargs) == 0:
                # This is a heuristic; we can't easily see the argument
                depends_get_db_count += 1

        if depends_get_db_count > 3:
            patterns["Depends_injection"] = depends_get_db_count

        if not patterns:
            return

        # Determine dominant pattern
        sum(patterns.values())
        has_get_db = "get_db" in patterns
        has_sessionmaker = "sessionmaker" in patterns or "SessionLocal" in patterns
        has_depends = "Depends_injection" in patterns

        if has_get_db and has_depends:
            title = "FastAPI-style session dependency injection"
            description = (
                f"Uses get_db() dependency pattern with Depends() for session lifecycle. "
                f"Found {patterns.get('get_db', 0)} get_db definitions."
            )
            confidence = 0.85
        elif has_sessionmaker:
            title = "sessionmaker-based session management"
            description = (
                f"Uses SQLAlchemy sessionmaker for session creation. "
                f"Found {patterns.get('sessionmaker', 0) + patterns.get('SessionLocal', 0)} usages."
            )
            confidence = 0.75
        else:
            title = "Mixed session lifecycle patterns"
            description = f"Session management patterns: {dict(patterns)}."
            confidence = 0.6

        # Build evidence
        evidence = []
        for pattern in ["get_db", "sessionmaker", "SessionLocal"]:
            if pattern in pattern_examples:
                for rel_path, line in pattern_examples[pattern][:2]:
                    ev = make_evidence(index, rel_path, line, radius=5)
                    if ev:
                        evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.db_session_lifecycle",
            category="database",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence[:ctx.max_evidence_snippets],
            stats=dict(patterns),
        ))

    def _detect_query_style(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect SQLAlchemy query style (1.x vs 2.0)."""
        # Check if SQLAlchemy is used
        sa_import_count = index.count_imports_matching("sqlalchemy")
        if sa_import_count < 2:
            return

        # Count query styles
        legacy_query_count = 0  # session.query(...)
        modern_select_count = 0  # select(...) / session.execute(select(...))
        legacy_examples: list[tuple[str, int]] = []
        modern_examples: list[tuple[str, int]] = []

        for rel_path, call in index.get_all_calls():
            # Legacy 1.x style: session.query(...) or db.query(...)
            if call.name.endswith(".query"):
                legacy_query_count += 1
                if len(legacy_examples) < 5:
                    legacy_examples.append((rel_path, call.line))

            # Modern 2.0 style: select(...)
            if call.name == "select":
                modern_select_count += 1
                if len(modern_examples) < 5:
                    modern_examples.append((rel_path, call.line))

        total = legacy_query_count + modern_select_count
        if total < 3:
            return

        legacy_ratio = legacy_query_count / total
        modern_ratio = modern_select_count / total

        if modern_ratio >= 0.8:
            title = "SQLAlchemy 2.0 select() style"
            description = (
                f"Uses modern SQLAlchemy 2.0 select() syntax. "
                f"{modern_select_count}/{total} queries use select()."
            )
            confidence = min(0.9, 0.6 + modern_ratio * 0.3)
            examples = modern_examples
        elif legacy_ratio >= 0.8:
            title = "SQLAlchemy 1.x Query style"
            description = (
                f"Uses legacy SQLAlchemy session.query() syntax. "
                f"{legacy_query_count}/{total} queries use .query()."
            )
            confidence = min(0.9, 0.6 + legacy_ratio * 0.3)
            examples = legacy_examples
        else:
            title = "Mixed SQLAlchemy query styles"
            description = (
                f"Uses both legacy .query() and modern select() styles. "
                f"Query: {legacy_query_count}, Select: {modern_select_count}."
            )
            confidence = 0.7
            examples = legacy_examples[:2] + modern_examples[:2]

        # Build evidence
        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.db_query_style",
            category="database",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "legacy_query_count": legacy_query_count,
                "modern_select_count": modern_select_count,
                "legacy_ratio": round(legacy_ratio, 3),
                "modern_ratio": round(modern_ratio, 3),
            },
        ))

    def _detect_transactions(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect transaction management patterns."""
        # Check if SQLAlchemy is used
        sa_import_count = index.count_imports_matching("sqlalchemy")
        if sa_import_count < 2:
            return

        # Count transaction patterns
        begin_count = 0
        begin_nested_count = 0
        commit_count = 0
        examples: list[tuple[str, int]] = []

        for rel_path, call in index.get_all_calls():
            if call.name.endswith(".begin"):
                begin_count += 1
                if len(examples) < 5:
                    examples.append((rel_path, call.line))
            elif call.name.endswith(".begin_nested"):
                begin_nested_count += 1
                if len(examples) < 5:
                    examples.append((rel_path, call.line))
            elif call.name.endswith(".commit"):
                commit_count += 1

        total_explicit = begin_count + begin_nested_count

        if total_explicit < 2 and commit_count < 3:
            return  # Not enough evidence

        if total_explicit >= 3:
            if begin_nested_count > begin_count:
                title = "Savepoint-based transaction nesting"
                description = (
                    f"Uses begin_nested() for savepoints. "
                    f"Found {begin_nested_count} begin_nested and {begin_count} begin calls."
                )
            else:
                title = "Explicit transaction management"
                description = (
                    f"Uses explicit transaction boundaries with session.begin(). "
                    f"Found {begin_count} begin and {begin_nested_count} begin_nested calls."
                )
            confidence = min(0.85, 0.5 + total_explicit * 0.05)
        else:
            title = "Implicit transaction management"
            description = (
                f"Relies on autocommit or implicit transactions. "
                f"Found {commit_count} explicit commit calls."
            )
            confidence = 0.6

        # Build evidence
        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.db_transactions",
            category="database",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "begin_count": begin_count,
                "begin_nested_count": begin_nested_count,
                "commit_count": commit_count,
            },
        ))

    def _detect_migrations(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect database migration tools (only if DB is used)."""
        # First check if database is actually used
        db_import_count = 0
        for lib_info in DB_LIBRARIES.values():
            for pattern in lib_info["imports"]:
                db_import_count += index.count_imports_matching(pattern)

        if db_import_count < 2:
            return  # No significant DB usage, don't check for migrations

        migration_tools: Counter[str] = Counter()
        migration_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # Alembic
            if "alembic" in imp.module:
                migration_tools["alembic"] += 1
                if "alembic" not in migration_examples:
                    migration_examples["alembic"] = []
                migration_examples["alembic"].append((rel_path, imp.line))

            # Django migrations
            if "django.db.migrations" in imp.module or "migrations" in imp.module:
                if "django" in imp.module:
                    migration_tools["django_migrations"] += 1
                    if "django_migrations" not in migration_examples:
                        migration_examples["django_migrations"] = []
                    migration_examples["django_migrations"].append((rel_path, imp.line))

            # yoyo-migrations
            if "yoyo" in imp.module:
                migration_tools["yoyo"] += 1
                if "yoyo" not in migration_examples:
                    migration_examples["yoyo"] = []
                migration_examples["yoyo"].append((rel_path, imp.line))

            # Tortoise aerich
            if "aerich" in imp.module:
                migration_tools["aerich"] += 1
                if "aerich" not in migration_examples:
                    migration_examples["aerich"] = []
                migration_examples["aerich"].append((rel_path, imp.line))

        # Check for alembic.ini or migrations directory
        for rel_path in index.files.keys():
            if "alembic.ini" in rel_path or "/migrations/" in rel_path or "/alembic/" in rel_path:
                migration_tools["alembic"] += 1
                if "alembic" not in migration_examples:
                    migration_examples["alembic"] = []

        if not migration_tools:
            return  # DB used but no migrations - that's fine, not all projects need them

        primary, primary_count = migration_tools.most_common(1)[0]

        tool_names = {
            "alembic": "Alembic",
            "django_migrations": "Django Migrations",
            "yoyo": "yoyo-migrations",
            "aerich": "Aerich (Tortoise)",
        }

        title = f"Database migrations: {tool_names.get(primary, primary)}"
        description = (
            f"Uses {tool_names.get(primary, primary)} for database migrations. "
            f"Found {primary_count} usages."
        )
        confidence = min(0.9, 0.6 + primary_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in migration_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.db_migrations",
            category="database",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "migration_tools": dict(migration_tools),
                "primary_tool": primary,
            },
        ))

    def _detect_connection_pooling(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect database connection pooling configuration."""
        # First check if SQLAlchemy is used (main lib with pooling config)
        sa_import_count = index.count_imports_matching("sqlalchemy")
        asyncpg_count = index.count_imports_matching("asyncpg")

        if sa_import_count < 2 and asyncpg_count < 2:
            return  # No significant DB usage

        pool_config: dict[str, int] = {}
        pool_examples: list[tuple[str, int]] = []

        for rel_path, call in index.get_all_calls():
            # Check for create_engine with pool config
            if "create_engine" in call.name or "create_async_engine" in call.name:
                pool_args = ["pool_size", "max_overflow", "pool_timeout", "pool_recycle", "pool_pre_ping"]
                has_pool_config = any(arg in call.kwargs for arg in pool_args)
                if has_pool_config:
                    pool_config["configured_pool"] = pool_config.get("configured_pool", 0) + 1
                    if len(pool_examples) < 5:
                        pool_examples.append((rel_path, call.line))
                else:
                    pool_config["default_pool"] = pool_config.get("default_pool", 0) + 1

            # Check for NullPool (serverless)
            if "NullPool" in call.name:
                pool_config["null_pool"] = pool_config.get("null_pool", 0) + 1
                if len(pool_examples) < 5:
                    pool_examples.append((rel_path, call.line))

            # Check for QueuePool explicitly
            if "QueuePool" in call.name:
                pool_config["queue_pool"] = pool_config.get("queue_pool", 0) + 1
                if len(pool_examples) < 5:
                    pool_examples.append((rel_path, call.line))

            # asyncpg pool
            if "create_pool" in call.name and asyncpg_count > 0:
                pool_config["asyncpg_pool"] = pool_config.get("asyncpg_pool", 0) + 1
                if len(pool_examples) < 5:
                    pool_examples.append((rel_path, call.line))

        if not pool_config:
            return  # No pool configuration detected

        if "configured_pool" in pool_config or "queue_pool" in pool_config:
            title = "Configured connection pooling"
            description = (
                f"Connection pooling is explicitly configured. "
                f"Found {pool_config.get('configured_pool', 0) + pool_config.get('queue_pool', 0)} configurations."
            )
            confidence = 0.85
        elif "null_pool" in pool_config:
            title = "NullPool for serverless"
            description = (
                f"Uses NullPool (no pooling) - suitable for serverless environments. "
                f"Found {pool_config['null_pool']} usages."
            )
            confidence = 0.8
        elif "asyncpg_pool" in pool_config:
            title = "asyncpg connection pool"
            description = (
                f"Uses asyncpg's built-in connection pooling. "
                f"Found {pool_config['asyncpg_pool']} pool creations."
            )
            confidence = 0.8
        else:
            title = "Default connection pooling"
            description = "Uses default SQLAlchemy connection pooling without explicit configuration."
            confidence = 0.6

        # Build evidence
        evidence = []
        for rel_path, line in pool_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.db_connection_pooling",
            category="database",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats=pool_config,
        ))

    def _detect_async_orm(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect async ORM usage patterns."""
        async_orm: str | None = None
        async_session_count = 0
        async_engine_count = 0
        async_examples: list[tuple[str, int]] = []
        is_async_framework = False

        # Check for async frameworks (FastAPI, Starlette, Quart)
        for rel_path, imp in index.get_all_imports():
            if any(f in imp.module for f in ("fastapi", "starlette", "quart", "aiohttp", "sanic")):
                is_async_framework = True
                break

        # Check for SQLAlchemy asyncio
        for rel_path, imp in index.get_all_imports():
            if "sqlalchemy.ext.asyncio" in imp.module:
                async_orm = "sqlalchemy_async"
                if "AsyncSession" in imp.names:
                    async_session_count += 1
                if "AsyncEngine" in imp.names or "create_async_engine" in imp.names:
                    async_engine_count += 1
                if len(async_examples) < 5:
                    async_examples.append((rel_path, imp.line))

            # Tortoise ORM (always async)
            if "tortoise" in imp.module and "tortoise" not in (async_orm or ""):
                async_orm = "tortoise"
                if len(async_examples) < 5:
                    async_examples.append((rel_path, imp.line))

            # databases library (async)
            if imp.module == "databases" or "databases" in imp.names:
                if async_orm != "sqlalchemy_async":
                    async_orm = "databases"
                if len(async_examples) < 5:
                    async_examples.append((rel_path, imp.line))

            # Check for AsyncSession usage in any import
            if "AsyncSession" in imp.names:
                async_session_count += 1

        # Count additional AsyncSession/AsyncEngine from calls
        for rel_path, call in index.get_all_calls():
            if "create_async_engine" in call.name:
                async_engine_count += 1
                if len(async_examples) < 5:
                    async_examples.append((rel_path, call.line))
            if "AsyncSession" in call.name:
                async_session_count += 1

        if not async_orm:
            return

        # Build title and description
        if async_orm == "sqlalchemy_async":
            title = "Async ORM: SQLAlchemy AsyncIO"
            description = (
                f"Uses SQLAlchemy's async extension for database access. "
                f"Found {async_session_count} AsyncSession and {async_engine_count} AsyncEngine usages."
            )
        elif async_orm == "tortoise":
            title = "Async ORM: Tortoise ORM"
            description = "Uses Tortoise ORM for async database access (native async ORM)."
        elif async_orm == "databases":
            title = "Async database: databases library"
            description = "Uses encode/databases for async database access."
        else:
            title = f"Async ORM: {async_orm}"
            description = f"Uses {async_orm} for async database access."

        # Adjust confidence based on framework match
        if is_async_framework and async_orm:
            confidence = 0.95
            description += " Async ORM matches async framework."
        else:
            confidence = 0.8

        # Build evidence
        evidence = []
        for rel_path, line in async_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.async_orm",
            category="database",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "async_orm": async_orm,
                "async_session_count": async_session_count,
                "async_engine_count": async_engine_count,
                "is_async_framework": is_async_framework,
            },
        ))

    def _detect_entities(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect database model entities (SQLAlchemy, Django, SQLModel)."""
        entities: list[dict[str, str]] = []
        orm = None

        for rel_path, cls in index.get_all_classes():
            # Skip test files
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role == "test":
                continue

            # Django models: inherits from models.Model
            if any("Model" in b for b in cls.bases) and any(
                "models" in b for b in cls.bases
            ):
                entities.append({"name": cls.name, "file": rel_path})
                orm = orm or "django"
                continue

            # SQLModel with table=True (check decorators / bases)
            if "SQLModel" in cls.bases:
                entities.append({"name": cls.name, "file": rel_path})
                orm = orm or "sqlmodel"
                continue

            # Check for __tablename__ in class body (SQLAlchemy declarative)
            if file_idx and file_idx.lines:
                # Scan lines after class def until next class/function def
                start = cls.line  # line after class declaration (0-indexed)
                end = min(len(file_idx.lines), start + 20)
                for line_text in file_idx.lines[start:end]:
                    stripped = line_text.lstrip()
                    # Stop at next class or top-level def
                    if stripped.startswith("class ") or (
                        stripped.startswith("def ") and not line_text.startswith(" ")
                    ):
                        break
                    if "__tablename__" in line_text:
                        entities.append({"name": cls.name, "file": rel_path})
                        orm = orm or "sqlalchemy"
                        break

        if not entities:
            return

        names = [e["name"] for e in entities[:10]]
        description = (
            f"{len(entities)} {orm or 'ORM'} models: {', '.join(names)}"
            + ("..." if len(entities) > 10 else "") + "."
        )

        result.rules.append(self.make_rule(
            rule_id="python.conventions.db_entities",
            category="database",
            title="Database entities",
            description=description,
            confidence=0.90,
            language="python",
            evidence=[],
            stats={
                "entities": entities,
                "entity_count": len(entities),
                "orm": orm or "unknown",
            },
        ))
