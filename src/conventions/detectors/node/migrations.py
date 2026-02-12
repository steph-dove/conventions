"""Node.js database migrations detector.

Detects migration tools: Prisma, TypeORM, Knex, Sequelize, Drizzle.
"""

from __future__ import annotations

import json
import re

from ...fs import read_file_safe
from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex

# Migration tool definitions
_MIGRATION_TOOLS = [
    {
        "name": "prisma",
        "config_files": ["prisma/schema.prisma"],
        "import_pattern": "@prisma/client",
        "migration_dirs": ["prisma/migrations"],
    },
    {
        "name": "typeorm",
        "config_files": ["ormconfig.json", "ormconfig.ts", "ormconfig.js"],
        "import_pattern": "typeorm",
        "migration_dirs": ["migrations", "src/migrations"],
    },
    {
        "name": "knex",
        "config_files": ["knexfile.js", "knexfile.ts"],
        "import_pattern": "knex",
        "migration_dirs": ["migrations"],
    },
    {
        "name": "sequelize",
        "config_files": [".sequelizerc"],
        "import_pattern": "sequelize",
        "migration_dirs": ["migrations", "db/migrations"],
    },
    {
        "name": "drizzle",
        "config_files": ["drizzle.config.ts", "drizzle.config.js"],
        "import_pattern": "drizzle-orm",
        "migration_dirs": ["drizzle"],
    },
]


@DetectorRegistry.register
class NodeMigrationsDetector(NodeDetector):
    """Detect Node.js database migration tools."""

    name = "node_migrations"
    description = "Detects database migration tools (Prisma, TypeORM, Knex, Sequelize, Drizzle)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect migration tools."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        detected_tools: list[dict[str, str | int | bool]] = []

        for tool_def in _MIGRATION_TOOLS:
            tool_info = self._check_tool(ctx, index, tool_def)
            if tool_info:
                detected_tools.append(tool_info)

        if detected_tools:
            primary = detected_tools[0]["name"]
            total_migrations = sum(int(t.get("migration_count", 0)) for t in detected_tools)

            tool_names = [str(t["name"]) for t in detected_tools]
            description = (
                f"Database migrations: {', '.join(tool_names)}. "
                f"{total_migrations} migration files found."
            )

            result.rules.append(self.make_rule(
                rule_id="node.conventions.db_migrations",
                category="database",
                title="Database migrations",
                description=description,
                confidence=0.90,
                language="node",
                evidence=[],
                stats={
                    "primary_tool": primary,
                    "tools": detected_tools,
                    "total_migration_files": total_migrations,
                },
            ))

        # Detect entities from Prisma schema, Mongoose models, or raw MongoDB
        self._detect_prisma_entities(ctx, result)
        if not any(r.id == "node.conventions.db_entities" for r in result.rules):
            self._detect_mongoose_entities(ctx, index, result)
        if not any(r.id == "node.conventions.db_entities" for r in result.rules):
            self._detect_mongodb_collections(ctx, index, result)

        return result

    def _check_tool(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        tool_def: dict,
    ) -> dict[str, str | int | bool] | None:
        """Check if a migration tool is present."""
        name = tool_def["name"]
        has_config = False
        has_import = False
        migration_count = 0

        # Check for config files
        for config_file in tool_def["config_files"]:
            if (ctx.repo_root / config_file).is_file():
                has_config = True
                break

        # Check for imports in indexed files
        import_pattern = tool_def["import_pattern"]
        for _, file_idx in index.files.items():
            for module, _ in file_idx.imports:
                if import_pattern in module:
                    has_import = True
                    break
            if has_import:
                break

        # Also check package.json dependencies
        if not has_import:
            pkg_json = ctx.repo_root / "package.json"
            if pkg_json.is_file():
                content = read_file_safe(pkg_json)
                if content:
                    try:
                        data = json.loads(content)
                        all_deps = {}
                        all_deps.update(data.get("dependencies", {}))
                        all_deps.update(data.get("devDependencies", {}))
                        if import_pattern in all_deps:
                            has_import = True
                    except (json.JSONDecodeError, ValueError):
                        pass

        if not has_config and not has_import:
            return None

        # Count migration files
        for migration_dir in tool_def["migration_dirs"]:
            mig_path = ctx.repo_root / migration_dir
            if mig_path.is_dir():
                for item in mig_path.iterdir():
                    if item.is_file() or item.is_dir():
                        migration_count += 1

        return {
            "name": name,
            "has_config": has_config,
            "has_import": has_import,
            "migration_count": migration_count,
        }

    def _detect_prisma_entities(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect database entities from Prisma schema."""
        schema_path = ctx.repo_root / "prisma" / "schema.prisma"
        if not schema_path.is_file():
            return

        content = read_file_safe(schema_path)
        if not content:
            return

        entities: list[dict[str, str]] = []
        for match in re.finditer(r"^model\s+(\w+)\s*\{", content, re.MULTILINE):
            entities.append({
                "name": match.group(1),
                "file": "prisma/schema.prisma",
            })

        if not entities:
            return

        names = [e["name"] for e in entities[:10]]
        description = (
            f"{len(entities)} Prisma models: {', '.join(names)}"
            + ("..." if len(entities) > 10 else "") + "."
        )

        result.rules.append(self.make_rule(
            rule_id="node.conventions.db_entities",
            category="database",
            title="Database entities",
            description=description,
            confidence=0.95,
            language="node",
            evidence=[],
            stats={
                "entities": entities,
                "entity_count": len(entities),
                "orm": "prisma",
            },
        ))

    def _detect_mongoose_entities(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect database entities from Mongoose schemas/models."""
        # Check if mongoose is used
        has_mongoose = False
        for _, file_idx in index.files.items():
            for module, _ in file_idx.imports:
                if "mongoose" in module:
                    has_mongoose = True
                    break
            if has_mongoose:
                break

        if not has_mongoose:
            # Also check package.json
            pkg_json = ctx.repo_root / "package.json"
            if pkg_json.is_file():
                content = read_file_safe(pkg_json)
                if content:
                    try:
                        data = json.loads(content)
                        all_deps = {}
                        all_deps.update(data.get("dependencies", {}))
                        all_deps.update(data.get("devDependencies", {}))
                        if "mongoose" in all_deps:
                            has_mongoose = True
                    except (json.JSONDecodeError, ValueError):
                        pass

        if not has_mongoose:
            return

        # Scan source files for mongoose.model() / new Schema() patterns
        entities: list[dict[str, str]] = []
        seen_names: set[str] = set()
        model_re = re.compile(
            r"""(?:mongoose\.model|model)\s*\(\s*['"](\w+)['"]""",
        )

        for rel_path, file_idx in index.files.items():
            if file_idx.role == "test":
                continue
            content = "\n".join(file_idx.lines)
            for match in model_re.finditer(content):
                name = match.group(1)
                if name not in seen_names:
                    seen_names.add(name)
                    entities.append({"name": name, "file": rel_path})

        if not entities:
            return

        names = [e["name"] for e in entities[:10]]
        description = (
            f"{len(entities)} Mongoose models: {', '.join(names)}"
            + ("..." if len(entities) > 10 else "") + "."
        )

        result.rules.append(self.make_rule(
            rule_id="node.conventions.db_entities",
            category="database",
            title="Database entities",
            description=description,
            confidence=0.90,
            language="node",
            evidence=[],
            stats={
                "entities": entities,
                "entity_count": len(entities),
                "orm": "mongoose",
            },
        ))

    def _detect_mongodb_collections(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect database entities from raw MongoDB driver collection access."""
        # Check if mongodb driver is used
        has_mongodb = False
        for _, file_idx in index.files.items():
            for module, _ in file_idx.imports:
                if module == "mongodb":
                    has_mongodb = True
                    break
            if has_mongodb:
                break

        if not has_mongodb:
            pkg_json = ctx.repo_root / "package.json"
            if pkg_json.is_file():
                content = read_file_safe(pkg_json)
                if content:
                    try:
                        data = json.loads(content)
                        all_deps = {}
                        all_deps.update(data.get("dependencies", {}))
                        all_deps.update(data.get("devDependencies", {}))
                        if "mongodb" in all_deps:
                            has_mongodb = True
                    except (json.JSONDecodeError, ValueError):
                        pass

        if not has_mongodb:
            return

        # Scan for db.collection('name') or .collection<Type>('name') patterns
        entities: list[dict[str, str]] = []
        seen_names: set[str] = set()
        collection_re = re.compile(
            r"""\.collection(?:<[^>]+>)?\s*\(\s*['"](\w+)['"]""",
        )

        for rel_path, file_idx in index.files.items():
            if file_idx.role == "test":
                continue
            content = "\n".join(file_idx.lines)
            for match in collection_re.finditer(content):
                name = match.group(1)
                if name not in seen_names:
                    seen_names.add(name)
                    entities.append({"name": name, "file": rel_path})

        if not entities:
            return

        names = [e["name"] for e in entities[:10]]
        description = (
            f"{len(entities)} MongoDB collections: {', '.join(names)}"
            + ("..." if len(entities) > 10 else "") + "."
        )

        result.rules.append(self.make_rule(
            rule_id="node.conventions.db_entities",
            category="database",
            title="Database entities",
            description=description,
            confidence=0.85,
            language="node",
            evidence=[],
            stats={
                "entities": entities,
                "entity_count": len(entities),
                "orm": "mongodb",
            },
        ))
