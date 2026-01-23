"""Generic repository layout detector (language-agnostic)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseDetector, DetectorContext, DetectorResult
from .registry import DetectorRegistry


@DetectorRegistry.register
class GenericRepoLayoutDetector(BaseDetector):
    """Detect common repository layout conventions."""

    name = "generic_repo_layout"
    description = "Detects repository structure conventions"
    languages: set[str] = set()  # Language-agnostic

    # Common directory patterns to look for
    LAYOUT_PATTERNS = {
        "src_layout": {
            "dirs": ["src"],
            "description": "Source code in src/ directory",
        },
        "tests_separate": {
            "dirs": ["tests", "test"],
            "description": "Tests in separate tests/ directory",
        },
        "docs_present": {
            "dirs": ["docs", "doc", "documentation"],
            "description": "Documentation directory present",
        },
        "ci_config": {
            "files": [".github/workflows", ".gitlab-ci.yml", ".circleci", "Jenkinsfile", ".travis.yml"],
            "description": "CI/CD configuration present",
        },
        "containerized": {
            "files": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
            "description": "Docker containerization configured",
        },
        "config_dir": {
            "dirs": ["config", "conf", "configs", "settings"],
            "description": "Configuration directory present",
        },
        "scripts_dir": {
            "dirs": ["scripts", "bin", "tools"],
            "description": "Scripts/tools directory present",
        },
    }

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect repository layout patterns."""
        result = DetectorResult()
        repo_root = ctx.repo_root

        detected_patterns: list[str] = []
        stats: dict[str, Any] = {}

        # Check each pattern
        for pattern_id, pattern_config in self.LAYOUT_PATTERNS.items():
            found = False

            # Check directories
            if "dirs" in pattern_config:
                for dir_name in pattern_config["dirs"]:
                    dir_path = repo_root / dir_name
                    if dir_path.is_dir():
                        found = True
                        break

            # Check files
            if "files" in pattern_config:
                for file_pattern in pattern_config["files"]:
                    file_path = repo_root / file_pattern
                    if file_path.exists():
                        found = True
                        break

            if found:
                detected_patterns.append(pattern_id)
                stats[pattern_id] = True
            else:
                stats[pattern_id] = False

        # Determine layout style
        if not detected_patterns:
            return result

        # Check for monorepo indicators
        is_monorepo = self._detect_monorepo(repo_root)
        stats["is_monorepo"] = is_monorepo

        # Build description based on detected patterns
        pattern_descriptions = [
            self.LAYOUT_PATTERNS[p]["description"]
            for p in detected_patterns
        ]

        if is_monorepo:
            title = "Monorepo structure detected"
            description = (
                f"Repository appears to be a monorepo. Detected patterns: "
                f"{', '.join(pattern_descriptions)}"
            )
        else:
            # Determine if src layout or flat layout
            if "src_layout" in detected_patterns:
                title = "Source layout (src/) structure"
                description = (
                    f"Repository uses src/ layout pattern. "
                    f"Additional patterns: {', '.join(pattern_descriptions)}"
                )
            else:
                title = "Flat project structure"
                description = (
                    f"Repository uses flat layout. "
                    f"Detected patterns: {', '.join(pattern_descriptions)}"
                )

        # Calculate confidence based on pattern count
        confidence = min(0.9, 0.5 + (len(detected_patterns) * 0.1))

        # Gather evidence
        evidence = []
        for pattern_id in detected_patterns[:ctx.max_evidence_snippets]:
            pattern_config = self.LAYOUT_PATTERNS[pattern_id]
            if "dirs" in pattern_config:
                for dir_name in pattern_config["dirs"]:
                    dir_path = repo_root / dir_name
                    if dir_path.is_dir():
                        # List first few items in directory as evidence
                        items = sorted(dir_path.iterdir())[:5]
                        if items:
                            from ..schemas import EvidenceSnippet
                            evidence.append(EvidenceSnippet(
                                file_path=dir_name,
                                line_start=1,
                                line_end=1,
                                excerpt=f"Directory contains: {', '.join(p.name for p in items)}",
                            ))
                        break
            elif "files" in pattern_config:
                for file_pattern in pattern_config["files"]:
                    file_path = repo_root / file_pattern
                    if file_path.exists() and file_path.is_file():
                        ev = self.make_evidence(ctx, file_path, 1, radius=10)
                        if ev:
                            evidence.append(ev)
                        break

        result.rules.append(self.make_rule(
            rule_id="repo.conventions.layout",
            category="structure",
            title=title,
            description=description,
            confidence=confidence,
            language=None,
            evidence=evidence,
            stats=stats,
        ))

        return result

    def _detect_monorepo(self, repo_root: Path) -> bool:
        """Detect if repository is a monorepo."""
        # Check for common monorepo indicators
        monorepo_indicators = [
            "packages",
            "apps",
            "services",
            "modules",
            "libs",
            "projects",
        ]

        indicator_count = 0
        for indicator in monorepo_indicators:
            indicator_path = repo_root / indicator
            if indicator_path.is_dir():
                # Check if it contains multiple subdirectories
                subdirs = [p for p in indicator_path.iterdir() if p.is_dir()]
                if len(subdirs) >= 2:
                    indicator_count += 1

        # Check for workspace files
        workspace_files = [
            "pnpm-workspace.yaml",
            "lerna.json",
            "rush.json",
            "nx.json",
            "turbo.json",
        ]
        for ws_file in workspace_files:
            if (repo_root / ws_file).exists():
                indicator_count += 1

        return indicator_count >= 1
