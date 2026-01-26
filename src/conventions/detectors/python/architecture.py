"""Python layering and import boundary conventions detector."""

from __future__ import annotations

from collections import Counter, defaultdict

import yaml

from ...fs import read_file_safe
from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonLayeringConventionsDetector(PythonDetector):
    """Detect Python layering and import boundary conventions."""

    name = "python_layering_conventions"
    description = "Detects module layering patterns and import boundaries"

    # Define allowed import directions (from -> to)
    # Standard layered architecture: api -> service -> db
    ALLOWED_DIRECTIONS = {
        "api": {"service", "schema", "other"},
        "service": {"db", "other"},
        "db": {"other"},
        "schema": {"other"},
        "test": {"api", "service", "db", "schema", "other"},  # Tests can import anything
    }

    # Violations to detect
    VIOLATIONS = {
        ("api", "db"): "API layer importing database layer directly",
        ("service", "api"): "Service layer importing API layer",
        ("db", "service"): "Database layer importing service layer",
        ("db", "api"): "Database layer importing API layer",
    }

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect module layering patterns and import boundaries."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Analyze import graph
        self._detect_layering_direction(ctx, index, result)

        # Detect boundary violations
        self._detect_boundary_violations(ctx, index, result)

        # Detect containerized local development
        self._detect_container_local_dev(ctx, result)

        return result

    def _detect_layering_direction(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect dominant import direction between layers."""
        # Build import graph by role
        role_imports: dict[str, Counter[str]] = defaultdict(Counter)
        import_examples: dict[tuple[str, str], list[tuple[str, int]]] = defaultdict(list)

        for rel_path, file_idx in index.files.items():
            source_role = file_idx.role

            for imp in file_idx.imports:
                # Try to determine the role of the imported module
                # This is heuristic - we look at the module name
                imported_role = self._infer_import_role(imp.module, imp.names)

                if imported_role and imported_role != source_role:
                    role_imports[source_role][imported_role] += 1

                    key = (source_role, imported_role)
                    if len(import_examples[key]) < 5:
                        import_examples[key].append((rel_path, imp.line))

        if not role_imports:
            return

        # Analyze layering pattern
        api_imports = role_imports.get("api", Counter())
        service_imports = role_imports.get("service", Counter())
        api_to_service = api_imports.get("service", 0)
        api_to_db = api_imports.get("db", 0)
        service_to_db = service_imports.get("db", 0)

        # Determine pattern
        total_deps = api_to_service + api_to_db + service_to_db

        if total_deps < 3:
            return  # Not enough evidence

        if api_to_service > 0 and service_to_db > 0 and api_to_db == 0:
            title = "Strict layered architecture (API -> Service -> DB)"
            description = (
                f"Clean separation of concerns with service layer abstraction. "
                f"API->Service: {api_to_service}, Service->DB: {service_to_db}, API->DB: {api_to_db}."
            )
            confidence = 0.9
        elif api_to_db > 0 and api_to_service == 0:
            title = "Direct data access pattern (API -> DB)"
            description = (
                f"API layer accesses database directly without service abstraction. "
                f"API->DB: {api_to_db}."
            )
            confidence = 0.8
        elif api_to_service > 0 and api_to_db > 0:
            title = "Mixed layering pattern"
            description = (
                f"API layer uses both service layer and direct DB access. "
                f"API->Service: {api_to_service}, API->DB: {api_to_db}, Service->DB: {service_to_db}."
            )
            confidence = 0.7
        else:
            title = "Loose layering structure"
            description = (
                f"Import patterns: {dict(role_imports)}."
            )
            confidence = 0.6

        # Build evidence
        evidence = []
        for (src, dst), examples in import_examples.items():
            if src == "api":
                for rel_path, line in examples[:2]:
                    ev = make_evidence(index, rel_path, line, radius=3)
                    if ev:
                        evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.layering_direction",
            category="architecture",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence[:ctx.max_evidence_snippets],
            stats={
                "api_to_service": api_to_service,
                "api_to_db": api_to_db,
                "service_to_db": service_to_db,
                "role_imports": {k: dict(v) for k, v in role_imports.items()},
            },
        ))

    def _detect_boundary_violations(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect imports that violate layering conventions."""
        violations: dict[tuple[str, str], list[tuple[str, int]]] = defaultdict(list)

        for rel_path, file_idx in index.files.items():
            source_role = file_idx.role

            if source_role == "test":
                continue  # Skip tests

            for imp in file_idx.imports:
                imported_role = self._infer_import_role(imp.module, imp.names)

                if imported_role:
                    key = (source_role, imported_role)
                    if key in self.VIOLATIONS:
                        violations[key].append((rel_path, imp.line))

        if not violations:
            return

        # Summarize violations
        total_violations = sum(len(v) for v in violations.values())
        violation_types = list(violations.keys())

        if len(violation_types) == 1:
            vtype = violation_types[0]
            title = f"Boundary violation: {self.VIOLATIONS[vtype]}"
            description = (
                f"Found {len(violations[vtype])} instances of {vtype[0]} -> {vtype[1]} imports."
            )
            confidence = min(0.85, 0.5 + len(violations[vtype]) * 0.05)
        else:
            title = "Multiple layering boundary violations"
            violation_summary = [
                f"{k[0]}->{k[1]}: {len(v)}" for k, v in violations.items()
            ]
            description = (
                f"Found {total_violations} boundary violations. "
                f"Types: {', '.join(violation_summary)}."
            )
            confidence = min(0.85, 0.5 + total_violations * 0.03)

        # Build evidence
        evidence = []
        for examples in violations.values():
            for rel_path, line in examples[:2]:
                ev = make_evidence(index, rel_path, line, radius=3)
                if ev:
                    evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.forbidden_imports",
            category="architecture",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence[:ctx.max_evidence_snippets],
            stats={
                "total_violations": total_violations,
                "violations_by_type": {
                    f"{k[0]}->{k[1]}": len(v) for k, v in violations.items()
                },
            },
        ))

    def _infer_import_role(self, module: str, names: list[str]) -> str | None:
        """Infer the role of an imported module."""
        module_lower = module.lower()
        names_lower = [n.lower() for n in names]

        # Database imports
        db_patterns = ["sqlalchemy", "database", "db", "model", "repository", "orm"]
        if any(p in module_lower for p in db_patterns):
            return "db"
        if any(p in n for p in ["session", "engine", "model"] for n in names_lower):
            return "db"

        # API imports
        api_patterns = ["router", "route", "api", "endpoint", "view", "handler"]
        if any(p in module_lower for p in api_patterns):
            return "api"

        # Service imports
        service_patterns = ["service", "business", "usecase", "domain"]
        if any(p in module_lower for p in service_patterns):
            return "service"

        # Schema imports
        schema_patterns = ["schema", "dto"]
        if any(p in module_lower for p in schema_patterns):
            return "schema"

        return None

    def _detect_container_local_dev(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect containerized local development setup."""
        has_compose = False
        has_devcontainer = False
        compose_services: list[str] = []
        compose_file: str | None = None

        # Check for docker-compose files
        compose_files = [
            ctx.repo_root / "docker-compose.yml",
            ctx.repo_root / "docker-compose.yaml",
            ctx.repo_root / "docker-compose.dev.yml",
            ctx.repo_root / "docker-compose.dev.yaml",
            ctx.repo_root / "compose.yml",
            ctx.repo_root / "compose.yaml",
        ]

        for compose_path in compose_files:
            if compose_path.is_file():
                has_compose = True
                compose_file = compose_path.name
                content = read_file_safe(compose_path)
                if content:
                    try:
                        compose_config = yaml.safe_load(content)
                        if compose_config and "services" in compose_config:
                            compose_services = list(compose_config["services"].keys())
                    except yaml.YAMLError:
                        pass
                break

        # Check for devcontainer
        devcontainer_path = ctx.repo_root / ".devcontainer" / "devcontainer.json"
        if devcontainer_path.is_file():
            has_devcontainer = True

        # Also check for devcontainer.json in root
        if not has_devcontainer:
            root_devcontainer = ctx.repo_root / ".devcontainer.json"
            if root_devcontainer.is_file():
                has_devcontainer = True

        if not has_compose and not has_devcontainer:
            return

        # Build title and description
        if has_devcontainer and has_compose:
            title = "Containerized dev: devcontainer + docker-compose"
            description = (
                f"Full containerized development setup with VS Code devcontainer and docker-compose. "
                f"Services: {', '.join(compose_services[:5]) if compose_services else 'configured'}."
            )
            confidence = 0.95
        elif has_devcontainer:
            title = "Containerized dev: VS Code devcontainer"
            description = "Uses VS Code devcontainer for development environment."
            confidence = 0.85
        elif has_compose and "dev" in (compose_file or ""):
            title = "Containerized dev: docker-compose (dev config)"
            description = (
                f"Uses docker-compose for development. "
                f"Services: {', '.join(compose_services[:5]) if compose_services else 'configured'}."
            )
            confidence = 0.85
        else:
            title = "Docker Compose setup"
            description = (
                f"Has docker-compose configuration. "
                f"Services: {', '.join(compose_services[:5]) if compose_services else 'configured'}."
            )
            confidence = 0.7

        result.rules.append(self.make_rule(
            rule_id="python.conventions.container_local_dev",
            category="architecture",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "has_compose": has_compose,
                "has_devcontainer": has_devcontainer,
                "compose_services": compose_services,
                "compose_file": compose_file,
            },
        ))
