"""Python security conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from .index import make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class PythonSecurityConventionsDetector(PythonDetector):
    """Detect Python security-related conventions."""

    name = "python_security_conventions"
    description = "Detects authentication patterns, raw SQL usage, and secrets access"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect authentication patterns, raw SQL usage, and secrets access."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect auth patterns
        self._detect_auth_pattern(ctx, index, result)

        # Detect raw SQL usage
        self._detect_raw_sql(ctx, index, result)

        # Detect secrets access patterns
        self._detect_secrets_access(ctx, index, result)

        return result

    def _detect_auth_pattern(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect authentication and authorization patterns."""
        auth_patterns: Counter[str] = Counter()
        auth_examples: dict[str, list[tuple[str, int]]] = {}

        # Check for auth-related imports
        for rel_path, imp in index.get_all_imports():
            # JWT libraries
            if any(x in imp.module for x in ["jwt", "jose", "pyjwt"]):
                auth_patterns["jwt"] += 1
                if "jwt" not in auth_examples:
                    auth_examples["jwt"] = []
                auth_examples["jwt"].append((rel_path, imp.line))

            # OAuth2
            if "oauth" in imp.module.lower() or "OAuth2PasswordBearer" in imp.names:
                auth_patterns["oauth2"] += 1
                if "oauth2" not in auth_examples:
                    auth_examples["oauth2"] = []
                auth_examples["oauth2"].append((rel_path, imp.line))

            # Passlib (password hashing)
            if "passlib" in imp.module:
                auth_patterns["passlib"] += 1
                if "passlib" not in auth_examples:
                    auth_examples["passlib"] = []
                auth_examples["passlib"].append((rel_path, imp.line))

            # bcrypt
            if imp.module == "bcrypt":
                auth_patterns["bcrypt"] += 1
                if "bcrypt" not in auth_examples:
                    auth_examples["bcrypt"] = []
                auth_examples["bcrypt"].append((rel_path, imp.line))

            # python-multipart (for form auth)
            if "python_multipart" in imp.module or "multipart" in imp.module:
                auth_patterns["form_auth"] += 1

        # Check for auth-related functions and dependencies
        for rel_path, func in index.get_all_functions():
            name_lower = func.name.lower()
            if any(x in name_lower for x in ["get_current_user", "authenticate", "verify_token", "requires_auth"]):
                auth_patterns["dependency_auth"] += 1
                if "dependency_auth" not in auth_examples:
                    auth_examples["dependency_auth"] = []
                auth_examples["dependency_auth"].append((rel_path, func.line))

        # Check for OAuth2PasswordBearer usage
        for rel_path, call in index.get_all_calls():
            if "OAuth2PasswordBearer" in call.name:
                auth_patterns["oauth2"] += 1
                if "oauth2" not in auth_examples:
                    auth_examples["oauth2"] = []
                auth_examples["oauth2"].append((rel_path, call.line))

        if not auth_patterns:
            return

        total = sum(auth_patterns.values())

        # Determine primary pattern
        if "jwt" in auth_patterns and auth_patterns["jwt"] > 0:
            title = "JWT-based authentication"
            description = (
                f"Uses JWT tokens for authentication. "
                f"JWT imports: {auth_patterns['jwt']}."
            )
            primary = "jwt"
        elif "oauth2" in auth_patterns:
            title = "OAuth2 authentication"
            description = (
                f"Uses OAuth2 for authentication. "
                f"OAuth2 usages: {auth_patterns['oauth2']}."
            )
            primary = "oauth2"
        elif "dependency_auth" in auth_patterns:
            title = "Dependency-based authentication"
            description = (
                f"Uses dependency injection for authentication (e.g., get_current_user). "
                f"Found {auth_patterns['dependency_auth']} auth dependencies."
            )
            primary = "dependency_auth"
        else:
            primary, primary_count = Counter(auth_patterns).most_common(1)[0]
            title = f"Authentication pattern: {primary}"
            description = f"Uses {primary} for authentication. Found {primary_count} usages."

        confidence = min(0.85, 0.5 + total * 0.03)

        # Build evidence
        evidence = []
        for key in [primary, "jwt", "oauth2", "dependency_auth"]:
            if key in auth_examples:
                for rel_path, line in auth_examples[key][:2]:
                    ev = make_evidence(index, rel_path, line, radius=5)
                    if ev:
                        evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.auth_pattern",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence[:ctx.max_evidence_snippets],
            stats=dict(auth_patterns),
        ))

    def _detect_raw_sql(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect raw SQL execution patterns."""
        raw_sql_count = 0
        parameterized_count = 0
        raw_sql_examples: list[tuple[str, int, str]] = []

        # Look for text() usage (SQLAlchemy raw SQL)
        for rel_path, call in index.get_all_calls():
            if call.name in ("text", "sqlalchemy.text"):
                raw_sql_count += 1
                if len(raw_sql_examples) < 10:
                    raw_sql_examples.append((rel_path, call.line, "text()"))

            # cursor.execute with string formatting is risky
            if call.name.endswith(".execute") and "cursor" in call.name.lower():
                raw_sql_count += 1
                if len(raw_sql_examples) < 10:
                    raw_sql_examples.append((rel_path, call.line, "cursor.execute"))

        # Also check for f-strings or .format() in SQL context
        # Build patterns dynamically to avoid self-matching when scanning this file
        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE"]
        fstring_patterns = []
        for kw in sql_keywords:
            fstring_patterns.append(f'f"{kw}')
            fstring_patterns.append(f"f'{kw}")

        for rel_path, file_idx in index.files.items():
            if file_idx.role == "test":
                continue

            content = "\n".join(file_idx.lines)

            # Look for potential SQL injection patterns
            # This is heuristic - look for SQL keywords near f-strings
            for pattern in fstring_patterns:
                if pattern in content:
                    raw_sql_count += 1

        if raw_sql_count < 2:
            return

        title = "Raw SQL execution detected"
        description = (
            f"Found {raw_sql_count} instances of raw SQL execution. "
            f"Consider using parameterized queries to prevent SQL injection."
        )
        confidence = min(0.85, 0.5 + raw_sql_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line, pattern in raw_sql_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.raw_sql_usage",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "raw_sql_count": raw_sql_count,
            },
        ))

    def _detect_secrets_access(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect how secrets/configuration is accessed."""
        patterns: Counter[str] = Counter()
        pattern_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, call in index.get_all_calls():
            # os.environ direct access
            if call.name in ("os.environ.get", "os.getenv", "os.environ"):
                patterns["os_environ"] += 1
                if "os_environ" not in pattern_examples:
                    pattern_examples["os_environ"] = []
                pattern_examples["os_environ"].append((rel_path, call.line))

            # Pydantic Settings
            if "Settings" in call.name or "BaseSettings" in call.name:
                patterns["pydantic_settings"] += 1
                if "pydantic_settings" not in pattern_examples:
                    pattern_examples["pydantic_settings"] = []
                pattern_examples["pydantic_settings"].append((rel_path, call.line))

        # Check for Pydantic BaseSettings inheritance
        for rel_path, cls in index.get_all_classes():
            if "BaseSettings" in cls.bases or "Settings" in cls.name:
                patterns["pydantic_settings"] += 1
                if "pydantic_settings" not in pattern_examples:
                    pattern_examples["pydantic_settings"] = []
                pattern_examples["pydantic_settings"].append((rel_path, cls.line))

        # Check for environ-config or dynaconf
        for rel_path, imp in index.get_all_imports():
            if "environs" in imp.module:
                patterns["environs"] += 1
            if "dynaconf" in imp.module:
                patterns["dynaconf"] += 1
            if "decouple" in imp.module:
                patterns["python_decouple"] += 1

        if not patterns:
            return

        primary, primary_count = patterns.most_common(1)[0]
        total = sum(patterns.values())

        pattern_names = {
            "os_environ": "os.environ direct access",
            "pydantic_settings": "Pydantic BaseSettings",
            "environs": "environs library",
            "dynaconf": "Dynaconf",
            "python_decouple": "python-decouple",
        }

        if "pydantic_settings" in patterns and patterns["pydantic_settings"] >= patterns.get("os_environ", 0):
            title = "Structured configuration with Pydantic Settings"
            description = (
                f"Uses Pydantic BaseSettings for configuration management. "
                f"Found {patterns['pydantic_settings']} Settings usages."
            )
            primary = "pydantic_settings"
            confidence = 0.85
        elif "os_environ" in patterns and patterns["os_environ"] > 3:
            title = "Direct environment variable access"
            description = (
                f"Accesses environment variables directly via os.environ/os.getenv. "
                f"Found {patterns['os_environ']} usages."
            )
            primary = "os_environ"
            confidence = 0.75
        else:
            title = f"Configuration via {pattern_names.get(primary, primary)}"
            description = f"Uses {pattern_names.get(primary, primary)}. Found {primary_count} usages."
            confidence = 0.7

        # Build evidence
        evidence = []
        for rel_path, line in pattern_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.secrets_access_style",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats=dict(patterns),
        ))
