"""Node.js architecture conventions detector."""

from __future__ import annotations

from pathlib import Path

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex, make_evidence


@DetectorRegistry.register
class NodeArchitectureDetector(NodeDetector):
    """Detect Node.js architecture conventions."""

    name = "node_architecture"
    description = "Detects Node.js project structure and architecture patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Node.js architecture conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect project structure
        self._detect_project_structure(ctx, index, result)

        # Detect layer separation
        self._detect_layer_separation(ctx, index, result)

        # Detect barrel exports
        self._detect_barrel_exports(ctx, index, result)

        return result

    def _detect_project_structure(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect project directory structure."""
        dirs: set[str] = set()

        for rel_path in index.files:
            parts = Path(rel_path).parts
            if len(parts) > 1:
                dirs.add(parts[0])

        has_src = "src" in dirs
        has_lib = "lib" in dirs
        has_routes = any(d in dirs for d in ("routes", "api"))
        has_controllers = "controllers" in dirs
        has_services = any(d in dirs for d in ("services", "service"))
        has_models = any(d in dirs for d in ("models", "entities"))

        structure_parts = []
        if has_src:
            structure_parts.append("src/")
        if has_lib:
            structure_parts.append("lib/")
        if has_routes:
            structure_parts.append("routes/")
        if has_controllers:
            structure_parts.append("controllers/")
        if has_services:
            structure_parts.append("services/")
        if has_models:
            structure_parts.append("models/")

        if len(structure_parts) < 2:
            return

        title = "Organized project structure"
        description = f"Uses organized directory structure: {', '.join(structure_parts)}."
        confidence = min(0.9, 0.6 + len(structure_parts) * 0.08)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.project_structure",
            category="architecture",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "has_src": has_src,
                "has_routes": has_routes,
                "has_controllers": has_controllers,
                "has_services": has_services,
                "has_models": has_models,
                "directories": list(structure_parts),
            },
        ))

    def _detect_layer_separation(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect MVC/service layer separation."""
        api_files = index.get_files_by_role("api")
        service_files = index.get_files_by_role("service")
        db_files = index.get_files_by_role("db")

        total_layered = len(api_files) + len(service_files) + len(db_files)

        if total_layered < 4:
            return

        # Calculate layer separation score
        layers = 0
        if len(api_files) >= 2:
            layers += 1
        if len(service_files) >= 2:
            layers += 1
        if len(db_files) >= 2:
            layers += 1

        if layers >= 3:
            title = "Full layer separation"
            description = (
                f"Clear separation: API ({len(api_files)}), "
                f"Service ({len(service_files)}), DB ({len(db_files)}) layers."
            )
            confidence = 0.9
        elif layers >= 2:
            title = "Partial layer separation"
            description = (
                f"Some layer separation: API ({len(api_files)}), "
                f"Service ({len(service_files)}), DB ({len(db_files)})."
            )
            confidence = 0.8
        else:
            return

        result.rules.append(self.make_rule(
            rule_id="node.conventions.layer_separation",
            category="architecture",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "api_files": len(api_files),
                "service_files": len(service_files),
                "db_files": len(db_files),
                "layer_count": layers,
            },
        ))

    def _detect_barrel_exports(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect barrel export pattern (index.ts re-exports)."""
        # Count index.ts/index.js files
        index_files = [
            f for f in index.files.values()
            if f.relative_path.endswith(("index.ts", "index.js", "index.mjs"))
        ]

        if len(index_files) < 3:
            return

        # Check for re-export patterns
        reexport_pattern = r'export\s+(?:\*|\{[^}]+\})\s+from'
        reexport_files = 0
        examples: list[tuple[str, int]] = []

        for file_idx in index_files:
            content = "\n".join(file_idx.lines)
            import re
            if re.search(reexport_pattern, content):
                reexport_files += 1
                # Find first re-export line
                for i, line_content in enumerate(file_idx.lines):
                    if re.search(reexport_pattern, line_content):
                        examples.append((file_idx.relative_path, i + 1))
                        break

        if reexport_files < 2:
            return

        title = "Barrel exports"
        description = (
            f"Uses barrel export pattern (index.ts re-exports). "
            f"Found {reexport_files} barrel files."
        )
        confidence = min(0.9, 0.6 + reexport_files * 0.05)

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=4)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.barrel_exports",
            category="architecture",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "index_files": len(index_files),
                "barrel_files": reexport_files,
            },
        ))
