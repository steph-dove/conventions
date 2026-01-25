"""Python decorator patterns detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonDecoratorPatternsDetector(PythonDetector):
    """Detect common decorator patterns in Python code."""

    name = "python_decorator_patterns"
    description = "Detects retry, caching, timing, auth, and other decorator patterns"

    # Common decorator categories
    RETRY_DECORATORS = {
        "retry", "retrying", "backoff", "tenacity", "retry_on_exception",
        "with_retries", "auto_retry",
    }

    CACHE_DECORATORS = {
        "cache", "lru_cache", "cached", "memoize", "memoized",
        "cached_property", "cache_page", "cache_control",
    }

    TIMING_DECORATORS = {
        "timer", "timed", "timeit", "measure_time", "profile",
        "track_time", "log_time", "timing",
    }

    AUTH_DECORATORS = {
        "login_required", "require_auth", "authenticated", "auth_required",
        "permission_required", "requires_auth", "protected", "secure",
        "require_role", "require_permission", "jwt_required", "token_required",
    }

    VALIDATION_DECORATORS = {
        "validate", "validator", "validate_input", "validate_args",
        "validate_call", "field_validator", "model_validator",
    }

    RATE_LIMIT_DECORATORS = {
        "rate_limit", "ratelimit", "throttle", "limit", "rate_limited",
    }

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect decorator patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_decorator_patterns(ctx, index, result)

        return result

    def _detect_decorator_patterns(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect common decorator usage patterns."""
        category_counts: Counter[str] = Counter()
        category_examples: dict[str, list[tuple[str, int, str]]] = {}
        specific_decorators: Counter[str] = Counter()

        for rel_path, dec in index.get_all_decorators():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            dec_name = dec.name.split(".")[-1].lower()  # Get last part, lowercase
            category = self._categorize_decorator(dec_name)

            if category:
                category_counts[category] += 1
                specific_decorators[dec.name] += 1

                if category not in category_examples:
                    category_examples[category] = []
                if len(category_examples[category]) < 5:
                    category_examples[category].append((rel_path, dec.line, dec.name))

        # Report each detected pattern category
        for category, count in category_counts.items():
            if count < 2:
                continue  # Need at least 2 usages

            title, description = self._get_category_info(category, count, specific_decorators)

            # Build evidence
            evidence = []
            for rel_path, line, name in category_examples.get(category, [])[:ctx.max_evidence_snippets]:
                ev = make_evidence(index, rel_path, line, radius=5)
                if ev:
                    evidence.append(ev)

            # Get the most common decorator in this category
            category_decorators = [
                (dec, c) for dec, c in specific_decorators.items()
                if self._categorize_decorator(dec.split(".")[-1].lower()) == category
            ]
            top_decorator = max(category_decorators, key=lambda x: x[1])[0] if category_decorators else ""

            result.rules.append(self.make_rule(
                rule_id=f"python.conventions.decorator_{category}",
                category="decorators",
                title=title,
                description=description,
                confidence=min(0.9, 0.5 + count * 0.05),
                language="python",
                evidence=evidence,
                stats={
                    "usage_count": count,
                    "top_decorator": top_decorator,
                    "category": category,
                },
            ))

        # Also detect custom/project-specific decorators
        self._detect_custom_decorators(ctx, index, result, category_counts)

    def _categorize_decorator(self, dec_name: str) -> str | None:
        """Categorize a decorator by its name."""
        if any(r in dec_name for r in self.RETRY_DECORATORS):
            return "retry"
        if any(c in dec_name for c in self.CACHE_DECORATORS):
            return "caching"
        if any(t in dec_name for t in self.TIMING_DECORATORS):
            return "timing"
        if any(a in dec_name for a in self.AUTH_DECORATORS):
            return "auth"
        if any(v in dec_name for v in self.VALIDATION_DECORATORS):
            return "validation"
        if any(r in dec_name for r in self.RATE_LIMIT_DECORATORS):
            return "rate_limit"
        return None

    def _get_category_info(
        self,
        category: str,
        count: int,
        specific_decorators: Counter,
    ) -> tuple[str, str]:
        """Get title and description for a decorator category."""
        info = {
            "retry": (
                "Retry decorator pattern",
                f"Uses retry decorators for resilient operations. Found {count} usages.",
            ),
            "caching": (
                "Caching decorator pattern",
                f"Uses caching decorators for memoization. Found {count} usages.",
            ),
            "timing": (
                "Timing/metrics decorator pattern",
                f"Uses timing decorators for performance monitoring. Found {count} usages.",
            ),
            "auth": (
                "Authentication decorator pattern",
                f"Uses decorators for authentication/authorization. Found {count} usages.",
            ),
            "validation": (
                "Validation decorator pattern",
                f"Uses decorators for input validation. Found {count} usages.",
            ),
            "rate_limit": (
                "Rate limiting decorator pattern",
                f"Uses rate limiting decorators. Found {count} usages.",
            ),
        }
        return info.get(category, (f"{category} decorator pattern", f"Found {count} usages."))

    def _detect_custom_decorators(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
        known_categories: Counter,
    ) -> None:
        """Detect project-specific custom decorators used frequently."""
        decorator_counts: Counter[str] = Counter()
        decorator_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, dec in index.get_all_decorators():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # Skip known framework decorators
            dec_lower = dec.name.lower()
            if any(skip in dec_lower for skip in [
                "route", "get", "post", "put", "delete", "patch",  # HTTP methods
                "app.", "router.",  # Framework
                "property", "staticmethod", "classmethod",  # Built-in
                "abstractmethod", "override",  # ABC
                "pytest", "fixture", "mark.",  # Testing
                "dataclass", "validator",  # Data classes
            ]):
                continue

            # Skip already categorized decorators
            dec_name = dec.name.split(".")[-1].lower()
            if self._categorize_decorator(dec_name):
                continue

            decorator_counts[dec.name] += 1
            if dec.name not in decorator_examples:
                decorator_examples[dec.name] = []
            if len(decorator_examples[dec.name]) < 5:
                decorator_examples[dec.name].append((rel_path, dec.line))

        # Find decorators used 3+ times (indicates a custom convention)
        custom_decorators = [
            (dec, count) for dec, count in decorator_counts.most_common(5)
            if count >= 3
        ]

        if not custom_decorators:
            return

        # Report top custom decorator
        top_decorator, top_count = custom_decorators[0]
        others = [d[0] for d in custom_decorators[1:3]]

        title = f"Custom decorator pattern: @{top_decorator}"
        description = f"Uses custom decorator @{top_decorator} ({top_count} usages)."
        if others:
            description += f" Also uses: {', '.join('@' + d for d in others)}."

        # Build evidence
        evidence = []
        for rel_path, line in decorator_examples.get(top_decorator, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.custom_decorators",
            category="decorators",
            title=title,
            description=description,
            confidence=min(0.85, 0.5 + top_count * 0.05),
            language="python",
            evidence=evidence,
            stats={
                "top_decorator": top_decorator,
                "usage_count": top_count,
                "other_custom_decorators": others,
            },
        ))
