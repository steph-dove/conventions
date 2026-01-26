"""Python tooling conventions detector (formatters, linters, import sorting)."""

from __future__ import annotations

import re

import yaml

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

        # Detect line length configuration
        self._detect_line_length(ctx, result)

        # Detect string quote style
        self._detect_string_quotes(ctx, result)

        # Detect pre-commit hooks
        self._detect_pre_commit_hooks(ctx, result)

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
        """Detect import sorting configuration with grouping analysis."""
        sorters: dict[str, dict] = {}
        has_grouping = False
        has_known_first_party = False
        profile = None
        has_sections = False
        has_force_sort_within_sections = False

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
                    # Extract profile
                    if "profile" in content:
                        match = re.search(r'profile\s*=\s*["\']?(\w+)', content)
                        if match:
                            profile = match.group(1)

                    # Check for known_first_party/known_third_party
                    if "known_first_party" in content or "known_third_party" in content:
                        has_known_first_party = True
                        has_grouping = True

                    # Check for sections configuration
                    if "sections" in content:
                        has_sections = True
                        has_grouping = True

                    # Check for force_sort_within_sections
                    if "force_sort_within_sections" in content:
                        has_force_sort_within_sections = True

                    sorters["isort"] = {
                        "name": "isort",
                        "config_file": config_file.name,
                        "profile": profile,
                        "has_grouping": has_grouping,
                    }
                    break

        # Ruff import sorting
        pyproject = ctx.repo_root / "pyproject.toml"
        ruff_toml = ctx.repo_root / "ruff.toml"

        for config_path in [pyproject, ruff_toml]:
            if config_path.is_file():
                content = read_file_safe(config_path)
                if not content:
                    continue

                # Check for I rules (import sorting)
                has_ruff_import = (
                    "[tool.ruff" in content
                    and ('"I"' in content or "'I'" in content or "I001" in content)
                )
                if config_path == ruff_toml:
                    has_ruff_import = '"I"' in content or "'I'" in content or "I001" in content

                if has_ruff_import:
                    # Check for isort configuration in ruff
                    if "[tool.ruff.lint.isort]" in content or "[lint.isort]" in content:
                        if "known-first-party" in content or "known-third-party" in content:
                            has_known_first_party = True
                            has_grouping = True
                        if "section" in content:
                            has_sections = True
                            has_grouping = True
                        if "force-sort-within-sections" in content:
                            has_force_sort_within_sections = True

                    sorters["ruff"] = {
                        "name": "Ruff (isort rules)",
                        "config_file": config_path.name,
                        "has_grouping": has_grouping,
                    }
                    break

        if not sorters:
            return

        sorter_names = [s["name"] for s in sorters.values()]
        primary = list(sorters.keys())[0]

        # Build title and description based on configuration quality
        if primary == "ruff" and has_grouping:
            title = "Import organization: Ruff with grouping"
            description = "Uses Ruff isort rules with proper import grouping. "
        elif primary == "isort" and profile == "black" and has_grouping:
            title = "Import organization: isort (black profile with grouping)"
            description = "Uses isort with Black profile and proper import grouping. "
        elif primary == "isort" and profile:
            title = f"Import organization: isort ({profile} profile)"
            description = f"Uses isort with {profile} profile. "
        else:
            title = f"Import sorting: {', '.join(sorter_names)}"
            description = f"Uses {', '.join(sorter_names)} for import organization. "

        if has_known_first_party:
            description += "Has first-party package configuration. "
        if has_sections:
            description += "Custom sections configured. "

        confidence = 0.95 if has_grouping else 0.85

        result.rules.append(self.make_rule(
            rule_id="python.conventions.import_sorting",
            category="tooling",
            title=title,
            description=description.strip(),
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "sorters": list(sorters.keys()),
                "primary_sorter": primary,
                "sorter_details": sorters,
                "has_grouping": has_grouping,
                "has_known_first_party": has_known_first_party,
                "has_sections": has_sections,
                "has_force_sort_within_sections": has_force_sort_within_sections,
                "profile": profile,
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

    def _detect_line_length(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect configured line length from various config files."""
        configured_length: int | None = None
        source: str | None = None

        # Check pyproject.toml for various tools
        pyproject = ctx.repo_root / "pyproject.toml"
        if pyproject.is_file():
            content = read_file_safe(pyproject)
            if content:
                # Check ruff line-length
                match = re.search(r'line-length\s*=\s*(\d+)', content)
                if match:
                    configured_length = int(match.group(1))
                    source = "pyproject.toml (ruff)"
                # Check black line-length
                if not configured_length:
                    match = re.search(r'\[tool\.black\].*?line-length\s*=\s*(\d+)', content, re.DOTALL)
                    if match:
                        configured_length = int(match.group(1))
                        source = "pyproject.toml (black)"

        # Check ruff.toml
        if not configured_length:
            ruff_toml = ctx.repo_root / "ruff.toml"
            if ruff_toml.is_file():
                content = read_file_safe(ruff_toml)
                if content:
                    match = re.search(r'line-length\s*=\s*(\d+)', content)
                    if match:
                        configured_length = int(match.group(1))
                        source = "ruff.toml"

        # Check setup.cfg for flake8
        if not configured_length:
            setup_cfg = ctx.repo_root / "setup.cfg"
            if setup_cfg.is_file():
                content = read_file_safe(setup_cfg)
                if content and "[flake8]" in content:
                    match = re.search(r'max-line-length\s*=\s*(\d+)', content)
                    if match:
                        configured_length = int(match.group(1))
                        source = "setup.cfg (flake8)"

        # Check .editorconfig
        if not configured_length:
            editorconfig = ctx.repo_root / ".editorconfig"
            if editorconfig.is_file():
                content = read_file_safe(editorconfig)
                if content:
                    # Look for max_line_length in Python section or global
                    match = re.search(r'max_line_length\s*=\s*(\d+)', content)
                    if match:
                        configured_length = int(match.group(1))
                        source = ".editorconfig"

        if configured_length is None:
            return

        is_88 = configured_length == 88

        if is_88:
            title = "Line length: 88 (Black default)"
            description = f"Line length is set to {configured_length} (Black/Ruff default). Source: {source}."
        elif configured_length in (100, 120):
            title = f"Line length: {configured_length}"
            description = f"Line length is set to {configured_length}. Source: {source}."
        elif configured_length == 79:
            title = "Line length: 79 (PEP 8)"
            description = f"Line length follows strict PEP 8 recommendation of 79. Source: {source}."
        else:
            title = f"Line length: {configured_length}"
            description = f"Line length is set to {configured_length}. Source: {source}."

        confidence = 0.9

        result.rules.append(self.make_rule(
            rule_id="python.conventions.line_length",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "configured_length": configured_length,
                "source": source,
                "is_88": is_88,
            },
        ))

    def _detect_string_quotes(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect configured string quote style from ruff/black config."""
        configured_style: str | None = None
        source: str | None = None

        # Check pyproject.toml
        pyproject = ctx.repo_root / "pyproject.toml"
        if pyproject.is_file():
            content = read_file_safe(pyproject)
            if content:
                # Check ruff format quote-style
                match = re.search(r'quote-style\s*=\s*["\'](\w+)["\']', content)
                if match:
                    configured_style = match.group(1).lower()
                    source = "pyproject.toml (ruff.format)"

                # Check ruff lint flake8-quotes
                if not configured_style:
                    if "[tool.ruff.lint.flake8-quotes]" in content:
                        match = re.search(r'inline-quotes\s*=\s*["\'](\w+)["\']', content)
                        if match:
                            configured_style = match.group(1).lower()
                            source = "pyproject.toml (ruff.lint.flake8-quotes)"

                # Check black skip-string-normalization (if True, no preference)
                if not configured_style:
                    if "skip-string-normalization" in content:
                        match = re.search(r'skip-string-normalization\s*=\s*(true|false)', content, re.IGNORECASE)
                        if match and match.group(1).lower() == "false":
                            configured_style = "double"
                            source = "pyproject.toml (black default)"

        # Check ruff.toml
        if not configured_style:
            ruff_toml = ctx.repo_root / "ruff.toml"
            if ruff_toml.is_file():
                content = read_file_safe(ruff_toml)
                if content:
                    match = re.search(r'quote-style\s*=\s*["\'](\w+)["\']', content)
                    if match:
                        configured_style = match.group(1).lower()
                        source = "ruff.toml"

        if configured_style is None:
            return

        if configured_style == "double":
            title = "String quotes: double (recommended)"
            description = f"Double quotes configured for strings. Source: {source}."
        elif configured_style == "single":
            title = "String quotes: single"
            description = f"Single quotes configured for strings. Source: {source}."
        else:
            title = f"String quotes: {configured_style}"
            description = f"Quote style configured as {configured_style}. Source: {source}."

        confidence = 0.85

        result.rules.append(self.make_rule(
            rule_id="python.conventions.string_quotes",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "configured_style": configured_style,
                "source": source,
            },
        ))

    def _detect_pre_commit_hooks(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect pre-commit hooks configuration."""
        pre_commit_config = ctx.repo_root / ".pre-commit-config.yaml"
        if not pre_commit_config.is_file():
            return

        content = read_file_safe(pre_commit_config)
        if not content:
            return

        try:
            config = yaml.safe_load(content)
        except yaml.YAMLError:
            return

        if not config or "repos" not in config:
            return

        hooks: list[str] = []
        has_ruff = False
        has_mypy = False
        has_pyright = False
        has_black = False
        has_flake8 = False
        has_isort = False

        for repo in config.get("repos", []):
            repo_url = repo.get("repo", "")
            for hook in repo.get("hooks", []):
                hook_id = hook.get("id", "")
                hooks.append(hook_id)

                if hook_id == "ruff" or "ruff" in repo_url:
                    has_ruff = True
                if hook_id in ("mypy", "mypy-strict"):
                    has_mypy = True
                if hook_id == "pyright":
                    has_pyright = True
                if hook_id == "black":
                    has_black = True
                if hook_id == "flake8":
                    has_flake8 = True
                if hook_id == "isort":
                    has_isort = True

        has_type_checker = has_mypy or has_pyright

        # Determine quality
        if has_ruff and has_type_checker:
            title = "Pre-commit hooks: ruff + type checker"
            description = f"Excellent pre-commit setup with ruff and {'mypy' if has_mypy else 'pyright'}. {len(hooks)} hooks configured."
            confidence = 0.95
        elif has_ruff:
            title = "Pre-commit hooks: ruff"
            description = f"Good pre-commit setup with ruff. {len(hooks)} hooks configured. Consider adding mypy/pyright."
            confidence = 0.85
        elif (has_black or has_flake8) and has_type_checker:
            title = "Pre-commit hooks: traditional + type checker"
            description = f"Pre-commit with {'black' if has_black else ''} {'flake8' if has_flake8 else ''} and type checker. {len(hooks)} hooks."
            confidence = 0.8
        elif has_black or has_flake8 or has_isort:
            title = "Pre-commit hooks: basic linting"
            description = f"Pre-commit with basic linting. {len(hooks)} hooks configured."
            confidence = 0.7
        else:
            title = "Pre-commit hooks configured"
            description = f"Pre-commit is configured with {len(hooks)} hooks."
            confidence = 0.6

        result.rules.append(self.make_rule(
            rule_id="python.conventions.pre_commit_hooks",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "has_pre_commit": True,
                "hooks": hooks,
                "has_ruff": has_ruff,
                "has_mypy": has_mypy,
                "has_pyright": has_pyright,
                "has_type_checker": has_type_checker,
                "has_black": has_black,
                "has_flake8": has_flake8,
                "has_isort": has_isort,
            },
        ))
