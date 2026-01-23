"""Go database migrations conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import GoDetector
from .index import make_evidence


@DetectorRegistry.register
class GoMigrationsDetector(GoDetector):
    """Detect Go database migration conventions."""

    name = "go_migrations"
    description = "Detects Go database migration tools (golang-migrate, goose, atlas)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go database migration conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        tools: dict[str, dict] = {}
        examples: dict[str, list[tuple[str, int]]] = {}

        # golang-migrate
        migrate_imports = index.find_imports_matching("github.com/golang-migrate/migrate", limit=20)
        if migrate_imports:
            tools["golang_migrate"] = {
                "name": "golang-migrate",
                "import_count": len(migrate_imports),
            }
            examples["golang_migrate"] = [(r, ln) for r, _, ln in migrate_imports[:5]]

        # goose
        goose_imports = index.find_imports_matching("github.com/pressly/goose", limit=20)
        if goose_imports:
            tools["goose"] = {
                "name": "goose",
                "import_count": len(goose_imports),
            }
            examples["goose"] = [(r, ln) for r, _, ln in goose_imports[:5]]

        # Atlas
        atlas_imports = index.find_imports_matching("ariga.io/atlas", limit=20)
        if atlas_imports:
            tools["atlas"] = {
                "name": "Atlas",
                "import_count": len(atlas_imports),
            }
            examples["atlas"] = [(r, ln) for r, _, ln in atlas_imports[:5]]

        # sql-migrate
        sql_migrate_imports = index.find_imports_matching("github.com/rubenv/sql-migrate", limit=20)
        if sql_migrate_imports:
            tools["sql_migrate"] = {
                "name": "sql-migrate",
                "import_count": len(sql_migrate_imports),
            }
            examples["sql_migrate"] = [(r, ln) for r, _, ln in sql_migrate_imports[:5]]

        # Check for migration files
        migration_dirs = [
            ctx.repo_root / "migrations",
            ctx.repo_root / "db" / "migrations",
            ctx.repo_root / "database" / "migrations",
        ]

        migration_file_count = 0
        for mig_dir in migration_dirs:
            if mig_dir.is_dir():
                # Count .sql files
                sql_files = list(mig_dir.glob("*.sql"))
                migration_file_count += len(sql_files)
                # Count .go files (Go-based migrations)
                go_files = list(mig_dir.glob("*.go"))
                migration_file_count += len(go_files)

        if not tools and migration_file_count == 0:
            return result

        if tools:
            [t["name"] for t in tools.values()]
            primary = max(tools, key=lambda k: tools[k]["import_count"])

            title = f"Database migrations: {tools[primary]['name']}"
            description = f"Uses {tools[primary]['name']} for database migrations."
            if migration_file_count > 0:
                description += f" {migration_file_count} migration file(s)."

            confidence = min(0.9, 0.7 + tools[primary]["import_count"] * 0.03)

            evidence = []
            for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
                ev = make_evidence(index, rel_path, line, radius=3)
                if ev:
                    evidence.append(ev)
        else:
            title = "SQL migration files"
            description = f"Has {migration_file_count} migration file(s) in migrations directory."
            confidence = 0.7
            evidence = []
            primary = "sql_files"
            tools = {"sql_files": {"name": "SQL files", "file_count": migration_file_count}}

        result.rules.append(self.make_rule(
            rule_id="go.conventions.migrations",
            category="database",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "tools": list(tools.keys()),
                "primary_tool": primary,
                "migration_file_count": migration_file_count,
                "tool_details": tools,
            },
        ))

        return result
