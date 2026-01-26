"""Python tooling conventions detector (formatters, linters, import sorting)."""

from __future__ import annotations

from ...fs import read_file_safe
from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry


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

        # Detect type checker strictness
        self._detect_type_checker_strictness(ctx, result)

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

        linter_names = [linter["name"] for linter in linters.values()]
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

    def _detect_type_checker_strictness(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect type checker configuration and strictness level."""
        type_checker = None
        strictness = "unknown"
        strict_options: list[str] = []
        config_file = None

        # Check mypy configuration
        mypy_configs = [
            (ctx.repo_root / "mypy.ini", "[mypy]"),
            (ctx.repo_root / ".mypy.ini", "[mypy]"),
            (ctx.repo_root / "pyproject.toml", "[tool.mypy]"),
            (ctx.repo_root / "setup.cfg", "[mypy]"),
        ]

        for config_path, section_marker in mypy_configs:
            if config_path.is_file():
                content = read_file_safe(config_path)
                if content and section_marker in content:
                    type_checker = "mypy"
                    config_file = config_path.name

                    # Check for strict mode
                    if "strict = true" in content.lower() or "strict=true" in content.lower():
                        strictness = "strict"
                        strict_options.append("strict mode")
                    else:
                        # Check individual strict options
                        strict_flags = [
                            ("disallow_untyped_defs", "disallow untyped defs"),
                            ("disallow_any_generics", "disallow any generics"),
                            ("warn_return_any", "warn return any"),
                            ("strict_equality", "strict equality"),
                            ("disallow_untyped_calls", "disallow untyped calls"),
                            ("check_untyped_defs", "check untyped defs"),
                            ("no_implicit_optional", "no implicit optional"),
                            ("warn_unused_ignores", "warn unused ignores"),
                        ]

                        for flag, name in strict_flags:
                            if f"{flag} = true" in content.lower() or f"{flag}=true" in content.lower():
                                strict_options.append(name)

                        if len(strict_options) >= 5:
                            strictness = "mostly_strict"
                        elif len(strict_options) >= 2:
                            strictness = "moderate"
                        elif strict_options:
                            strictness = "basic"
                        else:
                            strictness = "minimal"
                    break

        # Check pyright configuration
        pyright_config = ctx.repo_root / "pyrightconfig.json"
        pyproject = ctx.repo_root / "pyproject.toml"

        if not type_checker:
            if pyright_config.is_file():
                content = read_file_safe(pyright_config)
                if content:
                    type_checker = "pyright"
                    config_file = "pyrightconfig.json"

                    if '"strict"' in content:
                        strictness = "strict"
                        strict_options.append("strict mode")
                    elif '"basic"' in content:
                        strictness = "basic"
                    elif '"standard"' in content:
                        strictness = "moderate"
            elif pyproject.is_file():
                content = read_file_safe(pyproject)
                if content and "[tool.pyright]" in content:
                    type_checker = "pyright"
                    config_file = "pyproject.toml"

                    if 'typeCheckingMode = "strict"' in content:
                        strictness = "strict"
                        strict_options.append("strict mode")
                    elif 'typeCheckingMode = "basic"' in content:
                        strictness = "basic"

        if not type_checker:
            return

        # Build title and description
        strictness_labels = {
            "strict": "strict mode",
            "mostly_strict": "mostly strict",
            "moderate": "moderate",
            "basic": "basic",
            "minimal": "minimal checks",
            "unknown": "configured",
        }

        title = f"Type checker: {type_checker} ({strictness_labels.get(strictness, strictness)})"

        if strictness == "strict":
            description = f"Uses {type_checker} in strict mode - catches the most type errors."
        elif strictness == "mostly_strict":
            description = f"Uses {type_checker} with {len(strict_options)} strict options enabled."
        elif strict_options:
            description = f"Uses {type_checker} with some strict options: {', '.join(strict_options[:3])}."
        else:
            description = f"Uses {type_checker} with {strictness} configuration."

        confidence = 0.9 if strictness == "strict" else 0.8

        result.rules.append(self.make_rule(
            rule_id="python.conventions.type_checker_strictness",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "type_checker": type_checker,
                "strictness": strictness,
                "strict_options": strict_options,
                "config_file": config_file,
            },
        ))
