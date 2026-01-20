"""Python database conventions detector."""

from __future__ import annotations

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
