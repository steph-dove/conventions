"""Go security conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult
from .base import GoDetector
from .index import GoIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class GoSecurityDetector(GoDetector):
    """Detect Go security conventions."""

    name = "go_security"
    description = "Detects Go security patterns and practices"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go security conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect SQL usage patterns
        self._detect_sql_patterns(ctx, index, result)

        # Detect configuration/secrets management
        self._detect_config_management(ctx, index, result)

        # Detect input validation
        self._detect_input_validation(ctx, index, result)

        return result

    def _detect_sql_patterns(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect SQL query patterns - parameterized vs string concatenation."""
        # Parameterized queries: db.Query("...", args) or db.Exec("...", args)
        param_pattern = r'(?:Query|Exec|QueryRow)\s*\([^,]+,\s*[^)]+\)'
        param_matches = index.search_pattern(param_pattern, limit=50, exclude_tests=True)
        param_count = len(param_matches)

        # Potential SQL injection: string concatenation
        # "SELECT ... " + variable, fmt.Sprintf("SELECT...")
        concat_pattern = r'(?:Query|Exec|QueryRow)\s*\(\s*(?:fmt\.Sprintf|[^"]+\+)'
        concat_count = index.count_pattern(concat_pattern, exclude_tests=True)

        total = param_count + concat_count
        if total < 3:
            return

        safe_ratio = param_count / total if total else 0

        if safe_ratio >= 0.9:
            title = "Parameterized SQL queries"
            description = (
                f"Uses parameterized queries for SQL. "
                f"Safe: {param_count}, Potential issues: {concat_count}."
            )
            confidence = 0.9
        elif safe_ratio >= 0.5:
            title = "Mixed SQL query patterns"
            description = (
                f"Uses both parameterized and concatenated SQL. "
                f"Parameterized: {param_count}, Concatenated: {concat_count}."
            )
            confidence = 0.75
        else:
            title = "SQL injection risk"
            description = (
                f"Uses string concatenation for SQL queries. "
                f"Concatenated: {concat_count}, Parameterized: {param_count}."
            )
            confidence = 0.8

        evidence = []
        for rel_path, line, _ in param_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.sql_injection",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "parameterized_count": param_count,
                "concatenated_count": concat_count,
                "safe_ratio": round(safe_ratio, 3),
            },
        ))

    def _detect_config_management(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect configuration/secrets management libraries."""
        config_libs = {
            "viper": "github.com/spf13/viper",
            "envconfig": "github.com/kelseyhightower/envconfig",
            "godotenv": "github.com/joho/godotenv",
            "cleanenv": "github.com/ilyakaznacheev/cleanenv",
            "koanf": "github.com/knadh/koanf",
        }

        lib_counts: Counter[str] = Counter()
        examples: dict[str, list[tuple[str, int]]] = {}

        for name, pkg in config_libs.items():
            imports = index.find_imports_matching(pkg, limit=20)
            if imports:
                lib_counts[name] = len(imports)
                examples[name] = [(r, l) for r, _, l in imports[:5]]

        if not lib_counts:
            # Check for os.Getenv usage
            env_pattern = r"os\.Getenv\("
            env_count = index.count_pattern(env_pattern, exclude_tests=True)
            if env_count >= 5:
                result.rules.append(self.make_rule(
                    rule_id="go.conventions.secrets_config",
                    category="security",
                    title="Environment variables for config",
                    description=(
                        f"Uses os.Getenv for configuration. "
                        f"Found {env_count} usages."
                    ),
                    confidence=0.7,
                    language="go",
                    evidence=[],
                    stats={"os_getenv_count": env_count},
                ))
            return

        primary, primary_count = lib_counts.most_common(1)[0]

        lib_names = {
            "viper": "Viper",
            "envconfig": "envconfig",
            "godotenv": "godotenv",
            "cleanenv": "cleanenv",
            "koanf": "koanf",
        }

        title = f"Config management with {lib_names.get(primary, primary)}"
        description = (
            f"Uses {lib_names.get(primary, primary)} for configuration. "
            f"Found in {primary_count} files."
        )
        confidence = min(0.9, 0.7 + primary_count * 0.03)

        evidence = []
        for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.secrets_config",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "config_library": primary,
                "library_counts": dict(lib_counts),
            },
        ))

    def _detect_input_validation(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect input validation library usage."""
        validation_libs = {
            "validator": "github.com/go-playground/validator",
            "ozzo": "github.com/go-ozzo/ozzo-validation",
            "govalidator": "github.com/asaskevich/govalidator",
        }

        lib_counts: Counter[str] = Counter()
        examples: dict[str, list[tuple[str, int]]] = {}

        for name, pkg in validation_libs.items():
            imports = index.find_imports_matching(pkg, limit=20)
            if imports:
                lib_counts[name] = len(imports)
                examples[name] = [(r, l) for r, _, l in imports[:5]]

        if not lib_counts:
            return

        primary, primary_count = lib_counts.most_common(1)[0]

        lib_names = {
            "validator": "go-playground/validator",
            "ozzo": "ozzo-validation",
            "govalidator": "govalidator",
        }

        title = f"Input validation with {lib_names.get(primary, primary)}"
        description = (
            f"Uses {lib_names.get(primary, primary)} for input validation. "
            f"Found in {primary_count} files."
        )
        confidence = min(0.9, 0.7 + primary_count * 0.03)

        evidence = []
        for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.input_validation",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "validation_library": primary,
                "library_counts": dict(lib_counts),
            },
        ))
