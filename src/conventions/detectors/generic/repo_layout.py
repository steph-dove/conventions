"""Generic repository layout conventions detector."""

from __future__ import annotations

from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry


@DetectorRegistry.register
class GenericRepoLayoutDetector(BaseDetector):
    """Detect generic repository layout conventions."""

    name = "generic_repo_layout"
    description = "Detects common repository layout patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect common repository layout patterns."""
        result = DetectorResult()

        # Check for common directories
        common_dirs = {
            "src": "source code",
            "lib": "library code",
            "tests": "tests",
            "test": "tests",
            "docs": "documentation",
            "doc": "documentation",
            "scripts": "scripts",
            "bin": "binaries/scripts",
            "config": "configuration",
            "configs": "configuration",
            "examples": "examples",
            "tools": "tooling",
            ".github": "GitHub configuration",
            ".circleci": "CircleCI configuration",
            ".gitlab": "GitLab configuration",
        }

        found_dirs = []
        for dir_name, purpose in common_dirs.items():
            dir_path = ctx.repo_root / dir_name
            if dir_path.is_dir():
                found_dirs.append((dir_name, purpose))

        if found_dirs:
            dir_list = [f"{d[0]} ({d[1]})" for d in found_dirs[:5]]
            description = f"Repository has standard directories: {', '.join(dir_list)}"
            if len(found_dirs) > 5:
                description += f" and {len(found_dirs) - 5} more"

            result.rules.append(self.make_rule(
                rule_id="generic.conventions.repo_layout",
                category="structure",
                title="Standard repository layout",
                description=description,
                confidence=min(0.9, 0.5 + len(found_dirs) * 0.05),
                language="generic",
                evidence=[],
                stats={
                    "found_directories": [d[0] for d in found_dirs],
                },
            ))

        # Check for common config files
        config_files = {
            "README.md": "documentation",
            "README.rst": "documentation",
            "LICENSE": "license",
            "LICENSE.md": "license",
            "LICENSE.txt": "license",
            "LICENSE.rst": "license",
            "CHANGES.rst": "changelog",
            "CHANGES.md": "changelog",
            "HISTORY.md": "changelog",
            "HISTORY.rst": "changelog",
            "CONTRIBUTING.md": "contributing guidelines",
            "CHANGELOG.md": "changelog",
            "CODE_OF_CONDUCT.md": "code of conduct",
            ".gitignore": "git configuration",
            ".editorconfig": "editor configuration",
            "Makefile": "build automation",
            "docker-compose.yml": "Docker Compose",
            "docker-compose.yaml": "Docker Compose",
            "Dockerfile": "Docker",
            ".pre-commit-config.yaml": "pre-commit hooks",
        }

        found_files = []
        for file_name, purpose in config_files.items():
            file_path = ctx.repo_root / file_name
            if file_path.is_file():
                found_files.append((file_name, purpose))

        if len(found_files) >= 3:
            file_list = [f[0] for f in found_files[:5]]
            description = f"Repository has standard files: {', '.join(file_list)}"
            if len(found_files) > 5:
                description += f" and {len(found_files) - 5} more"

            result.rules.append(self.make_rule(
                rule_id="generic.conventions.standard_files",
                category="structure",
                title="Standard repository files",
                description=description,
                confidence=min(0.85, 0.4 + len(found_files) * 0.05),
                language="generic",
                evidence=[],
                stats={
                    "found_files": [f[0] for f in found_files],
                },
            ))

        return result
