"""Python retries and timeouts conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonRetriesTimeoutsConventionsDetector(PythonDetector):
    """Detect Python retry and timeout conventions."""

    name = "python_retries_timeouts_conventions"
    description = "Detects retry patterns and timeout usage in external calls"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect retry patterns and timeout usage in external calls."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect retry patterns
        self._detect_retries(ctx, index, result)

        # Detect timeout patterns
        self._detect_timeouts(ctx, index, result)

        return result

    def _detect_retries(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect retry library and pattern usage."""
        retry_libs: Counter[str] = Counter()
        retry_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # tenacity
            if "tenacity" in imp.module or "tenacity" in imp.names:
                retry_libs["tenacity"] += 1
                if "tenacity" not in retry_examples:
                    retry_examples["tenacity"] = []
                retry_examples["tenacity"].append((rel_path, imp.line))

            # backoff
            if imp.module == "backoff" or "backoff" in imp.names:
                retry_libs["backoff"] += 1
                if "backoff" not in retry_examples:
                    retry_examples["backoff"] = []
                retry_examples["backoff"].append((rel_path, imp.line))

            # retrying
            if imp.module == "retrying" or "retrying" in imp.names:
                retry_libs["retrying"] += 1
                if "retrying" not in retry_examples:
                    retry_examples["retrying"] = []
                retry_examples["retrying"].append((rel_path, imp.line))

            # urllib3 retry
            if "urllib3" in imp.module and "Retry" in imp.names:
                retry_libs["urllib3_retry"] += 1
                if "urllib3_retry" not in retry_examples:
                    retry_examples["urllib3_retry"] = []
                retry_examples["urllib3_retry"].append((rel_path, imp.line))

        # Check for retry decorators
        for rel_path, dec in index.get_all_decorators():
            if "retry" in dec.name.lower():
                if "tenacity" in dec.name or "retry" == dec.name:
                    retry_libs["tenacity"] += 1
                elif "backoff" in dec.name:
                    retry_libs["backoff"] += 1

        if not retry_libs:
            return

        # Determine pattern
        primary, primary_count = retry_libs.most_common(1)[0]
        total = sum(retry_libs.values())

        lib_names = {
            "tenacity": "tenacity",
            "backoff": "backoff",
            "retrying": "retrying",
            "urllib3_retry": "urllib3 Retry",
        }

        if len(retry_libs) == 1:
            title = f"Uses {lib_names.get(primary, primary)} for retries"
            description = (
                f"Uses {lib_names.get(primary, primary)} library for retry logic. "
                f"Found {primary_count} usages."
            )
            confidence = min(0.9, 0.6 + primary_count * 0.05)
        else:
            other_libs = [lib_names.get(lib, lib) for lib in retry_libs if lib != primary]
            title = f"Retry handling with {lib_names.get(primary, primary)}"
            description = (
                f"Uses {lib_names.get(primary, primary)} ({primary_count}/{total}). "
                f"Also uses: {', '.join(other_libs)}."
            )
            confidence = min(0.8, 0.5 + total * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in retry_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.retries",
            category="resilience",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "retry_library_counts": dict(retry_libs),
                "primary_library": primary,
            },
        ))

    def _detect_timeouts(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect timeout usage in HTTP clients and async calls."""
        timeout_indicators = 0
        no_timeout_indicators = 0
        timeout_examples: list[tuple[str, int, str]] = []

        # HTTP client libraries that should have timeouts
        http_clients = {"httpx", "requests", "aiohttp", "urllib3"}

        # Check for HTTP client imports and timeout usage
        http_client_files = set()
        for rel_path, imp in index.get_all_imports():
            for client in http_clients:
                if client in imp.module:
                    http_client_files.add(rel_path)

        # Check for timeout argument in calls
        for rel_path, call in index.get_all_calls():
            # Check for explicit timeout argument
            if "timeout" in call.kwargs:
                timeout_indicators += 1
                if len(timeout_examples) < 10:
                    timeout_examples.append((rel_path, call.line, call.name))

            # Check for Client/Session creation with timeout
            if any(x in call.name for x in ["Client", "Session", "get", "post", "request"]):
                if rel_path in http_client_files:
                    if "timeout" not in call.kwargs:
                        no_timeout_indicators += 1

        # Check for asyncio.wait_for
        for rel_path, call in index.get_all_calls():
            if "wait_for" in call.name:
                timeout_indicators += 1
                if len(timeout_examples) < 10:
                    timeout_examples.append((rel_path, call.line, "asyncio.wait_for"))

        total = timeout_indicators + no_timeout_indicators
        if total < 3:
            return

        timeout_ratio = timeout_indicators / total if total else 0

        if timeout_ratio >= 0.7:
            title = "Consistent timeout usage"
            description = (
                f"Timeouts are commonly specified on external calls. "
                f"Found {timeout_indicators} calls with explicit timeouts."
            )
            confidence = min(0.85, 0.5 + timeout_ratio * 0.35)
        elif timeout_ratio >= 0.3:
            title = "Inconsistent timeout usage"
            description = (
                f"Timeouts are sometimes specified. "
                f"{timeout_indicators} with timeout, {no_timeout_indicators} without."
            )
            confidence = 0.7
        else:
            title = "Infrequent timeout specification"
            description = (
                f"Timeouts are rarely specified on external calls. "
                f"Only {timeout_indicators} calls with explicit timeouts."
            )
            confidence = 0.6

        # Build evidence
        evidence = []
        for rel_path, line, name in timeout_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.timeouts",
            category="resilience",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "timeout_indicators": timeout_indicators,
                "no_timeout_indicators": no_timeout_indicators,
                "timeout_ratio": round(timeout_ratio, 3),
            },
        ))
