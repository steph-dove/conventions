"""Python security conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


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

        # Detect rate limiting (only for web APIs)
        self._detect_rate_limiting(ctx, index, result)

        # Detect password hashing
        self._detect_password_hashing(ctx, index, result)

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
            if file_idx.role in ("test", "docs"):
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
        sum(patterns.values())

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

    def _detect_rate_limiting(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect rate limiting (only if web API framework is used)."""
        # First check if this is a web API project
        api_frameworks = ["fastapi", "flask", "django", "starlette", "aiohttp", "falcon"]
        api_import_count = 0
        for framework in api_frameworks:
            api_import_count += index.count_imports_matching(framework)

        if api_import_count < 2:
            return  # Not a web API project, rate limiting not relevant

        rate_limit_libs: Counter[str] = Counter()
        rate_limit_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # slowapi (FastAPI/Starlette)
            if "slowapi" in imp.module:
                rate_limit_libs["slowapi"] += 1
                if "slowapi" not in rate_limit_examples:
                    rate_limit_examples["slowapi"] = []
                rate_limit_examples["slowapi"].append((rel_path, imp.line))

            # flask-limiter
            if "flask_limiter" in imp.module:
                rate_limit_libs["flask_limiter"] += 1
                if "flask_limiter" not in rate_limit_examples:
                    rate_limit_examples["flask_limiter"] = []
                rate_limit_examples["flask_limiter"].append((rel_path, imp.line))

            # django-ratelimit
            if "django_ratelimit" in imp.module or "ratelimit" in imp.module:
                rate_limit_libs["django_ratelimit"] += 1
                if "django_ratelimit" not in rate_limit_examples:
                    rate_limit_examples["django_ratelimit"] = []
                rate_limit_examples["django_ratelimit"].append((rel_path, imp.line))

            # limits library
            if imp.module == "limits" or "limits" in imp.names:
                rate_limit_libs["limits"] += 1
                if "limits" not in rate_limit_examples:
                    rate_limit_examples["limits"] = []
                rate_limit_examples["limits"].append((rel_path, imp.line))

            # aiohttp-ratelimiter
            if "aiohttp_ratelimiter" in imp.module:
                rate_limit_libs["aiohttp_ratelimiter"] += 1

        # Check for rate limit decorators
        for rel_path, dec in index.get_all_decorators():
            if "limit" in dec.name.lower() or "rate" in dec.name.lower():
                rate_limit_libs["decorator_usage"] = rate_limit_libs.get("decorator_usage", 0) + 1

        if not rate_limit_libs:
            return  # No rate limiting detected - this is okay, we don't dock points

        # Filter out just decorator usage count for library detection
        lib_counts = {k: v for k, v in rate_limit_libs.items() if k != "decorator_usage"}
        if not lib_counts:
            return

        primary, primary_count = Counter(lib_counts).most_common(1)[0]
        decorator_count = rate_limit_libs.get("decorator_usage", 0)

        lib_names = {
            "slowapi": "SlowAPI",
            "flask_limiter": "Flask-Limiter",
            "django_ratelimit": "django-ratelimit",
            "limits": "limits",
            "aiohttp_ratelimiter": "aiohttp-ratelimiter",
        }

        title = f"Rate limiting: {lib_names.get(primary, primary)}"
        if decorator_count > 0:
            description = (
                f"Uses {lib_names.get(primary, primary)} for rate limiting. "
                f"Found {decorator_count} rate limit decorators."
            )
            confidence = min(0.9, 0.6 + decorator_count * 0.05)
        else:
            description = (
                f"Imports {lib_names.get(primary, primary)} rate limiting library. "
                f"Found {primary_count} imports."
            )
            confidence = min(0.75, 0.5 + primary_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in rate_limit_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.rate_limiting",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "rate_limit_library_counts": dict(lib_counts),
                "primary_library": primary,
                "decorator_usage_count": decorator_count,
            },
        ))

    def _detect_password_hashing(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect password hashing libraries (only if auth patterns exist)."""
        # First check if this project has authentication
        auth_indicators = 0
        for rel_path, imp in index.get_all_imports():
            if any(x in imp.module for x in ["jwt", "jose", "oauth", "passlib", "bcrypt", "argon2"]):
                auth_indicators += 1

        for rel_path, func in index.get_all_functions():
            if any(x in func.name.lower() for x in ["password", "hash", "verify", "authenticate", "login"]):
                auth_indicators += 1

        if auth_indicators < 2:
            return  # No significant auth usage, password hashing not relevant

        hash_libs: Counter[str] = Counter()
        hash_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # argon2-cffi (best)
            if "argon2" in imp.module:
                hash_libs["argon2"] += 1
                if "argon2" not in hash_examples:
                    hash_examples["argon2"] = []
                hash_examples["argon2"].append((rel_path, imp.line))

            # bcrypt
            if imp.module == "bcrypt" or "bcrypt" in imp.names:
                hash_libs["bcrypt"] += 1
                if "bcrypt" not in hash_examples:
                    hash_examples["bcrypt"] = []
                hash_examples["bcrypt"].append((rel_path, imp.line))

            # passlib
            if "passlib" in imp.module:
                hash_libs["passlib"] += 1
                if "passlib" not in hash_examples:
                    hash_examples["passlib"] = []
                hash_examples["passlib"].append((rel_path, imp.line))

            # hashlib (weak for passwords)
            if imp.module == "hashlib":
                hash_libs["hashlib"] += 1
                if "hashlib" not in hash_examples:
                    hash_examples["hashlib"] = []
                hash_examples["hashlib"].append((rel_path, imp.line))

        # Check for CryptContext (passlib best practice)
        for rel_path, call in index.get_all_calls():
            if "CryptContext" in call.name:
                hash_libs["passlib_cryptcontext"] = hash_libs.get("passlib_cryptcontext", 0) + 1
                if "passlib_cryptcontext" not in hash_examples:
                    hash_examples["passlib_cryptcontext"] = []
                hash_examples["passlib_cryptcontext"].append((rel_path, call.line))

        if not hash_libs:
            return  # No password hashing detected

        # Determine primary and quality
        primary, primary_count = hash_libs.most_common(1)[0]

        lib_names = {
            "argon2": "argon2-cffi",
            "bcrypt": "bcrypt",
            "passlib": "passlib",
            "passlib_cryptcontext": "passlib CryptContext",
            "hashlib": "hashlib",
        }

        # Quality assessment
        if "argon2" in hash_libs:
            quality = "excellent"
            title = "Password hashing: argon2 (recommended)"
        elif "bcrypt" in hash_libs or "passlib_cryptcontext" in hash_libs:
            quality = "good"
            title = f"Password hashing: {lib_names.get(primary, primary)}"
        elif "passlib" in hash_libs:
            quality = "good"
            title = "Password hashing: passlib"
        elif "hashlib" in hash_libs:
            quality = "weak"
            title = "Password hashing: hashlib (not recommended)"
        else:
            quality = "unknown"
            title = f"Password hashing: {lib_names.get(primary, primary)}"

        description = f"Uses {lib_names.get(primary, primary)} for password hashing."
        if quality == "weak":
            description += " Consider using argon2 or bcrypt for better security."

        confidence = min(0.85, 0.6 + primary_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in hash_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.password_hashing",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "hash_library_counts": dict(hash_libs),
                "primary_library": primary,
                "quality": quality,
            },
        ))
