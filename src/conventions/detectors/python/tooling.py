"""Python tooling conventions detector (formatters, linters, import sorting)."""

from __future__ import annotations

from pathlib import Path

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from ...fs import read_file_safe


@DetectorRegistry.register
class PythonToolingDetector(PythonDetector):
    """Detect Python tooling conventions (formatters, linters)."""

    name = "python_tooling"
    description = "Detects Python formatters, linters, and import sorting tools"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Python tooling conventions."""
        result = DetectorResult()

        # Detect formatter
        self._detect_formatter(ctx, result)

        # Detect linter
        self._detect_linter(ctx, result)

        # Detect import sorting
        self._detect_import_sorting(ctx, result)

        return result

    def _detect_formatter(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect Python code formatter configuration."""
        formatters: dict[str, dict] = {}

        # Black
        black_configs = [
            ctx.repo_root / "pyproject.toml",
            ctx.repo_root / ".black",
        ]
        for config_file in black_configs:
            if config_file.is_file():
                content = read_file_safe(config_file)
                if content and "[tool.black]" in content:
                    formatters["black"] = {
                        "name": "Black",
                        "config_file": config_file.name,
                    }
                    break

        # Ruff formatter
        pyproject = ctx.repo_root / "pyproject.toml"
        ruff_toml = ctx.repo_root / "ruff.toml"
        if pyproject.is_file():
            content = read_file_safe(pyproject)
            if content and "[tool.ruff]" in content:
                # Check if ruff format is enabled
                if "format" in content.lower():
                    formatters["ruff"] = {
                        "name": "Ruff",
                        "config_file": "pyproject.toml",
                    }
        if ruff_toml.is_file():
            formatters["ruff"] = {
                "name": "Ruff",
                "config_file": "ruff.toml",
            }

        # YAPF
        yapf_configs = [
            ctx.repo_root / ".style.yapf",
            ctx.repo_root / "setup.cfg",
            ctx.repo_root / "pyproject.toml",
        ]
        for config_file in yapf_configs:
            if config_file.is_file():
                content = read_file_safe(config_file)
                if content and ("[yapf]" in content or "[tool.yapf]" in content):
                    formatters["yapf"] = {
                        "name": "YAPF",
                        "config_file": config_file.name,
                    }
                    break

        # autopep8
        autopep8_configs = [
            ctx.repo_root / ".pep8",
            ctx.repo_root / "setup.cfg",
            ctx.repo_root / "tox.ini",
        ]
        for config_file in autopep8_configs:
            if config_file.is_file():
                content = read_file_safe(config_file)
                if content and "[autopep8]" in content:
                    formatters["autopep8"] = {
                        "name": "autopep8",
                        "config_file": config_file.name,
                    }
                    break

        if not formatters:
            return

        formatter_names = [f["name"] for f in formatters.values()]
        primary = list(formatters.keys())[0]

        if len(formatters) == 1:
            title = f"Formatter: {formatters[primary]['name']}"
            description = f"Uses {formatters[primary]['name']} for code formatting."
        else:
            title = f"Formatters: {', '.join(formatter_names)}"
            description = f"Uses multiple formatters: {', '.join(formatter_names)}."

        confidence = 0.9 if primary in ("black", "ruff") else 0.8

        result.rules.append(self.make_rule(
            rule_id="python.conventions.formatter",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "formatters": list(formatters.keys()),
                "primary_formatter": primary,
                "formatter_details": formatters,
            },
        ))

    def _detect_linter(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect Python linter configuration."""
        linters: dict[str, dict] = {}

        # Ruff (modern, fast)
        pyproject = ctx.repo_root / "pyproject.toml"
        ruff_toml = ctx.repo_root / "ruff.toml"
        if pyproject.is_file():
            content = read_file_safe(pyproject)
            if content and "[tool.ruff" in content:
                # Extract some settings
                rules = []
                if "select" in content:
                    rules.append("custom rules")
                if "ignore" in content:
                    rules.append("ignores configured")
                linters["ruff"] = {
                    "name": "Ruff",
                    "config_file": "pyproject.toml",
                    "features": rules,
                }
        if ruff_toml.is_file():
            linters["ruff"] = {
                "name": "Ruff",
                "config_file": "ruff.toml",
            }

        # Flake8
        flake8_configs = [
            ctx.repo_root / ".flake8",
            ctx.repo_root / "setup.cfg",
            ctx.repo_root / "tox.ini",
        ]
        for config_file in flake8_configs:
            if config_file.is_file():
                content = read_file_safe(config_file)
                if content and "[flake8]" in content:
                    linters["flake8"] = {
                        "name": "Flake8",
                        "config_file": config_file.name,
                    }
                    break

        # Pylint
        pylint_configs = [
            ctx.repo_root / ".pylintrc",
            ctx.repo_root / "pylintrc",
            ctx.repo_root / "pyproject.toml",
        ]
        for config_file in pylint_configs:
            if config_file.is_file():
                content = read_file_safe(config_file)
                if content and ("[pylint" in content.lower() or "[tool.pylint]" in content):
                    linters["pylint"] = {
                        "name": "Pylint",
                        "config_file": config_file.name,
                    }
                    break

        # mypy (type checker)
        mypy_configs = [
            ctx.repo_root / "mypy.ini",
            ctx.repo_root / ".mypy.ini",
            ctx.repo_root / "pyproject.toml",
        ]
        for config_file in mypy_configs:
            if config_file.is_file():
                content = read_file_safe(config_file)
                if content and ("[mypy" in content or "[tool.mypy]" in content):
                    linters["mypy"] = {
                        "name": "mypy",
                        "config_file": config_file.name,
                    }
                    break

        # pyright / pyrightconfig.json
        pyright_config = ctx.repo_root / "pyrightconfig.json"
        if pyright_config.is_file():
            linters["pyright"] = {
                "name": "Pyright",
                "config_file": "pyrightconfig.json",
            }

        if not linters:
            return

        linter_names = [l["name"] for l in linters.values()]
        primary = list(linters.keys())[0]

        title = f"Linters: {', '.join(linter_names)}"
        description = f"Uses {', '.join(linter_names)} for code quality."
        confidence = min(0.95, 0.7 + len(linters) * 0.1)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.linter",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "linters": list(linters.keys()),
                "primary_linter": primary,
                "linter_details": linters,
            },
        ))

    def _detect_import_sorting(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect import sorting configuration."""
        sorters: dict[str, dict] = {}

        # isort
        isort_configs = [
            ctx.repo_root / ".isort.cfg",
            ctx.repo_root / "pyproject.toml",
            ctx.repo_root / "setup.cfg",
        ]
        for config_file in isort_configs:
            if config_file.is_file():
                content = read_file_safe(config_file)
                if content and ("[isort]" in content or "[tool.isort]" in content):
                    profile = None
                    if "profile" in content:
                        import re
                        match = re.search(r'profile\s*=\s*["\']?(\w+)', content)
                        if match:
                            profile = match.group(1)
                    sorters["isort"] = {
                        "name": "isort",
                        "config_file": config_file.name,
                        "profile": profile,
                    }
                    break

        # Ruff import sorting
        pyproject = ctx.repo_root / "pyproject.toml"
        if pyproject.is_file():
            content = read_file_safe(pyproject)
            if content and "[tool.ruff" in content:
                # Check for I rules (import sorting)
                if '"I"' in content or "'I'" in content or "I001" in content:
                    sorters["ruff"] = {
                        "name": "Ruff (isort rules)",
                        "config_file": "pyproject.toml",
                    }

        if not sorters:
            return

        sorter_names = [s["name"] for s in sorters.values()]
        primary = list(sorters.keys())[0]

        title = f"Import sorting: {', '.join(sorter_names)}"
        description = f"Uses {', '.join(sorter_names)} for import organization."
        if sorters.get("isort", {}).get("profile"):
            description += f" Profile: {sorters['isort']['profile']}."

        confidence = 0.9

        result.rules.append(self.make_rule(
            rule_id="python.conventions.import_sorting",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "sorters": list(sorters.keys()),
                "primary_sorter": primary,
                "sorter_details": sorters,
            },
        ))
