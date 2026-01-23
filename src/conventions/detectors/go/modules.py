"""Go module management conventions detector."""

from __future__ import annotations

import re
from pathlib import Path

from ..base import DetectorContext, DetectorResult
from .base import GoDetector
from ..registry import DetectorRegistry
from ...fs import read_file_safe


@DetectorRegistry.register
class GoModulesDetector(GoDetector):
    """Detect Go module management conventions."""

    name = "go_modules"
    description = "Detects Go module configuration and dependency management"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go module management conventions."""
        result = DetectorResult()

        go_mod = ctx.repo_root / "go.mod"
        if not go_mod.is_file():
            return result

        content = read_file_safe(go_mod)
        if content is None:
            return result

        # Parse go.mod
        go_version = None
        module_name = None
        direct_deps = 0
        indirect_deps = 0
        replace_count = 0
        retract_count = 0

        for line in content.splitlines():
            line = line.strip()

            # Go version
            if line.startswith("go "):
                go_version = line.split()[1] if len(line.split()) > 1 else None

            # Module name
            if line.startswith("module "):
                module_name = line.split()[1] if len(line.split()) > 1 else None

            # Count dependencies
            if line.startswith("require") or (line and not line.startswith(("//", "go ", "module ", "replace", "retract", "exclude", ")"))):
                if "// indirect" in line:
                    indirect_deps += 1
                elif re.match(r'^\S+\s+v', line):
                    direct_deps += 1

            # Replace directives
            if line.startswith("replace"):
                replace_count += 1

            # Retract directives
            if line.startswith("retract"):
                retract_count += 1

        # Check for go.sum
        go_sum = ctx.repo_root / "go.sum"
        has_sum = go_sum.is_file()

        # Check for vendor directory
        vendor_dir = ctx.repo_root / "vendor"
        has_vendor = vendor_dir.is_dir()

        # Build description
        parts = []
        if go_version:
            parts.append(f"Go {go_version}")
        parts.append(f"{direct_deps} direct deps")
        if indirect_deps:
            parts.append(f"{indirect_deps} indirect")
        if has_vendor:
            parts.append("vendored")

        title = "Go Modules"
        description = f"Uses Go modules. {', '.join(parts)}."

        if replace_count > 0:
            description += f" {replace_count} replace directive(s)."

        # Assess module hygiene
        hygiene_score = 0
        if has_sum:
            hygiene_score += 1
        if go_version:
            hygiene_score += 1
        if replace_count == 0:  # No local replaces is good for production
            hygiene_score += 1
        if indirect_deps <= direct_deps * 3:  # Reasonable indirect ratio
            hygiene_score += 1

        confidence = min(0.95, 0.7 + hygiene_score * 0.05)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.modules",
            category="dependencies",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=[],
            stats={
                "go_version": go_version,
                "module_name": module_name,
                "direct_deps": direct_deps,
                "indirect_deps": indirect_deps,
                "replace_count": replace_count,
                "retract_count": retract_count,
                "has_sum": has_sum,
                "has_vendor": has_vendor,
            },
        ))

        return result
