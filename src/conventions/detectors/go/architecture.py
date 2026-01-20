"""Go architecture conventions detector."""

from __future__ import annotations

from pathlib import Path

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import GoDetector
from .index import GoIndex, make_evidence


@DetectorRegistry.register
class GoArchitectureDetector(GoDetector):
    """Detect Go architecture conventions."""

    name = "go_architecture"
    description = "Detects Go project structure and architecture patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go architecture conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect standard Go project layout
        self._detect_package_structure(ctx, index, result)

        # Detect interface segregation
        self._detect_interface_patterns(ctx, index, result)

        # Detect dependency direction
        self._detect_dependency_direction(ctx, index, result)

        return result

    def _detect_package_structure(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect standard Go project layout (cmd/, internal/, pkg/)."""
        dirs: set[str] = set()

        for rel_path in index.files:
            parts = Path(rel_path).parts
            if len(parts) > 1:
                dirs.add(parts[0])

        has_cmd = "cmd" in dirs
        has_internal = "internal" in dirs
        has_pkg = "pkg" in dirs
        has_api = "api" in dirs

        standard_dirs = sum([has_cmd, has_internal, has_pkg])
        if standard_dirs < 2:
            return

        structure_parts = []
        if has_cmd:
            structure_parts.append("cmd/")
        if has_internal:
            structure_parts.append("internal/")
        if has_pkg:
            structure_parts.append("pkg/")
        if has_api:
            structure_parts.append("api/")

        title = "Standard Go project layout"
        description = (
            f"Follows standard Go project structure. "
            f"Uses: {', '.join(structure_parts)}."
        )
        confidence = min(0.95, 0.7 + standard_dirs * 0.1)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.package_structure",
            category="architecture",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=[],
            stats={
                "has_cmd": has_cmd,
                "has_internal": has_internal,
                "has_pkg": has_pkg,
                "has_api": has_api,
            },
        ))

    def _detect_interface_patterns(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect interface segregation patterns (small interfaces)."""
        interface_sizes: list[int] = []
        examples: list[tuple[str, int]] = []

        for file_idx in index.get_non_test_files():
            content = "\n".join(file_idx.lines)

            # Find interface definitions and count methods
            # type X interface { ... }
            import re
            for match in re.finditer(
                r'type\s+(\w+)\s+interface\s*\{([^}]*)\}',
                content,
                re.DOTALL,
            ):
                match.group(1)
                interface_body = match.group(2)

                # Count method signatures (lines with parentheses)
                methods = len(re.findall(r'\w+\s*\([^)]*\)', interface_body))
                interface_sizes.append(methods)

                if methods <= 3 and len(examples) < 20:
                    line = content[:match.start()].count("\n") + 1
                    examples.append((file_idx.relative_path, line))

        if len(interface_sizes) < 3:
            return

        avg_size = sum(interface_sizes) / len(interface_sizes)
        small_interfaces = sum(1 for s in interface_sizes if s <= 3)
        small_ratio = small_interfaces / len(interface_sizes)

        if small_ratio >= 0.7:
            title = "Small interfaces (ISP)"
            description = (
                f"Follows interface segregation with small interfaces. "
                f"{small_interfaces}/{len(interface_sizes)} have ≤3 methods. "
                f"Avg size: {avg_size:.1f} methods."
            )
            confidence = min(0.9, 0.7 + small_ratio * 0.2)
        elif small_ratio >= 0.4:
            title = "Mixed interface sizes"
            description = (
                f"Mix of small and large interfaces. "
                f"{small_interfaces}/{len(interface_sizes)} have ≤3 methods. "
                f"Avg size: {avg_size:.1f} methods."
            )
            confidence = 0.7
        else:
            title = "Large interfaces"
            description = (
                f"Tends toward larger interfaces. "
                f"Only {small_interfaces}/{len(interface_sizes)} have ≤3 methods. "
                f"Avg size: {avg_size:.1f} methods."
            )
            confidence = 0.65

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.interface_segregation",
            category="architecture",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "total_interfaces": len(interface_sizes),
                "small_interfaces": small_interfaces,
                "average_methods": round(avg_size, 2),
                "small_ratio": round(small_ratio, 3),
            },
        ))

    def _detect_dependency_direction(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect dependency direction (internal not importing cmd, etc.)."""
        # Count imports from internal/ to cmd/ (should be 0)
        internal_imports_cmd = 0
        pkg_imports_internal = 0

        for rel_path, file_idx in index.files.items():
            parts = Path(rel_path).parts
            if not parts:
                continue

            is_internal = parts[0] == "internal"
            is_pkg = parts[0] == "pkg"

            for pkg, _ in file_idx.imports:
                # Check if internal imports cmd
                if is_internal and "/cmd/" in pkg:
                    internal_imports_cmd += 1
                # Check if pkg imports internal
                if is_pkg and "/internal/" in pkg:
                    pkg_imports_internal += 1

        # This is a negative check - if violations exist, report them
        violations = internal_imports_cmd + pkg_imports_internal
        if violations > 0:
            result.rules.append(self.make_rule(
                rule_id="go.conventions.dependency_direction",
                category="architecture",
                title="Dependency direction violations",
                description=(
                    f"Found dependency direction issues. "
                    f"internal→cmd: {internal_imports_cmd}, pkg→internal: {pkg_imports_internal}."
                ),
                confidence=0.85,
                language="go",
                evidence=[],
                stats={
                    "internal_imports_cmd": internal_imports_cmd,
                    "pkg_imports_internal": pkg_imports_internal,
                },
            ))
        elif "internal" in {Path(r).parts[0] for r in index.files if Path(r).parts}:
            # No violations and using internal/
            result.rules.append(self.make_rule(
                rule_id="go.conventions.dependency_direction",
                category="architecture",
                title="Clean dependency direction",
                description="Maintains proper dependency direction with internal/ packages.",
                confidence=0.85,
                language="go",
                evidence=[],
                stats={
                    "internal_imports_cmd": 0,
                    "pkg_imports_internal": 0,
                },
            ))
