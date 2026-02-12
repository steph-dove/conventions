"""Code ownership conventions detector.

Detects CODEOWNERS patterns and file change hotspots.
"""

from __future__ import annotations

import subprocess

from ...fs import read_file_safe
from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry


@DetectorRegistry.register
class CodeOwnershipDetector(BaseDetector):
    """Detect code ownership patterns."""

    name = "generic_code_ownership"
    description = "Detects CODEOWNERS rules and file change hotspots"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect code ownership patterns."""
        result = DetectorResult()

        self._detect_codeowners(ctx, result)
        self._detect_file_hotspots(ctx, result)

        return result

    def _detect_codeowners(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Parse CODEOWNERS file."""
        codeowners_path = None
        for candidate in (
            "CODEOWNERS",
            ".github/CODEOWNERS",
            "docs/CODEOWNERS",
            ".gitlab/CODEOWNERS",
        ):
            p = ctx.repo_root / candidate
            if p.is_file():
                codeowners_path = p
                break

        if codeowners_path is None:
            return

        content = read_file_safe(codeowners_path)
        if not content:
            return

        owners: set[str] = set()
        rules: list[dict[str, str | list[str]]] = []

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            pattern = parts[0]
            rule_owners = parts[1:]
            owners.update(rule_owners)
            rules.append({"pattern": pattern, "owners": rule_owners})

        if not rules:
            return

        description = (
            f"CODEOWNERS defines {len(rules)} rules with {len(owners)} unique owners."
        )

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.code_owners",
            category="governance",
            title="Code ownership",
            description=description,
            confidence=0.95,
            language="generic",
            evidence=[],
            stats={
                "rule_count": len(rules),
                "owner_count": len(owners),
                "owners": sorted(owners),
                "rules": rules[:20],
            },
        ))

    def _detect_file_hotspots(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect frequently changed files via git log."""
        # Check if this is a git repo
        git_dir = ctx.repo_root / ".git"
        if not git_dir.exists():
            return

        try:
            proc = subprocess.run(
                ["git", "log", "--format=", "--name-only", "-100"],
                capture_output=True,
                text=True,
                cwd=ctx.repo_root,
                timeout=10,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return

        if proc.returncode != 0:
            return

        file_counts: dict[str, int] = {}
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            file_counts[line] = file_counts.get(line, 0) + 1

        if not file_counts:
            return

        # Top 10 hotspots — sort by change count descending
        sorted_files = sorted(file_counts.items(), key=lambda x: -x[1])[:10]
        hotspots = [{"file": f, "changes": c} for f, c in sorted_files]

        if not hotspots or sorted_files[0][1] < 3:
            return

        description = (
            f"Top hotspot: {hotspots[0]['file']} ({hotspots[0]['changes']} changes in last 100 commits)."
        )

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.file_hotspots",
            category="governance",
            title="File change hotspots",
            description=description,
            confidence=0.80,
            language="generic",
            evidence=[],
            stats={
                "hotspots": hotspots,
                "total_files_changed": len(file_counts),
            },
        ))
