"""Python resilience conventions detector."""

from __future__ import annotations

import re
from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonResilienceConventionsDetector(PythonDetector):
    """Detect Python resilience conventions (retries, timeouts, circuit breakers, health checks)."""

    name = "python_resilience_conventions"
    description = "Detects retry patterns, timeout usage, circuit breakers, and health check endpoints"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect resilience patterns in Python code."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect retry patterns
        self._detect_retries(ctx, index, result)

        # Detect timeout patterns
        self._detect_timeouts(ctx, index, result)

        # Detect circuit breakers
        self._detect_circuit_breakers(ctx, index, result)

        # Detect health check endpoints
        self._detect_health_checks(ctx, index, result)

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

    def _detect_circuit_breakers(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect circuit breaker library usage."""
        cb_libs: Counter[str] = Counter()
        cb_examples: dict[str, list[tuple[str, int]]] = {}
        circuit_breaker_count = 0

        for rel_path, imp in index.get_all_imports():
            # pybreaker
            if "pybreaker" in imp.module or "pybreaker" in imp.names:
                cb_libs["pybreaker"] += 1
                if "pybreaker" not in cb_examples:
                    cb_examples["pybreaker"] = []
                cb_examples["pybreaker"].append((rel_path, imp.line))

            # circuitbreaker
            if imp.module == "circuitbreaker" or "circuitbreaker" in imp.names:
                cb_libs["circuitbreaker"] += 1
                if "circuitbreaker" not in cb_examples:
                    cb_examples["circuitbreaker"] = []
                cb_examples["circuitbreaker"].append((rel_path, imp.line))

            # aiobreaker
            if "aiobreaker" in imp.module or "aiobreaker" in imp.names:
                cb_libs["aiobreaker"] += 1
                if "aiobreaker" not in cb_examples:
                    cb_examples["aiobreaker"] = []
                cb_examples["aiobreaker"].append((rel_path, imp.line))

        # Check for circuit breaker decorators
        for rel_path, dec in index.get_all_decorators():
            dec_lower = dec.name.lower()
            if "circuit" in dec_lower or "breaker" in dec_lower:
                circuit_breaker_count += 1

        # Check for CircuitBreaker instantiation
        for rel_path, call in index.get_all_calls():
            if "CircuitBreaker" in call.name or "circuit_breaker" in call.name.lower():
                circuit_breaker_count += 1
                # Try to associate with a library
                if cb_libs:
                    primary = cb_libs.most_common(1)[0][0]
                    if primary not in cb_examples:
                        cb_examples[primary] = []
                    if len(cb_examples[primary]) < 10:
                        cb_examples[primary].append((rel_path, call.line))

        if not cb_libs:
            return

        # Determine primary library
        primary, primary_count = cb_libs.most_common(1)[0]

        lib_names = {
            "pybreaker": "pybreaker",
            "circuitbreaker": "circuitbreaker",
            "aiobreaker": "aiobreaker",
        }

        if circuit_breaker_count > 0:
            title = f"Circuit breakers with {lib_names.get(primary, primary)}"
            description = (
                f"Uses {lib_names.get(primary, primary)} for circuit breakers. "
                f"Found {circuit_breaker_count} circuit breaker(s) defined."
            )
            confidence = min(0.9, 0.6 + circuit_breaker_count * 0.05)
        else:
            title = f"Circuit breaker library: {lib_names.get(primary, primary)}"
            description = (
                f"Imports {lib_names.get(primary, primary)} circuit breaker library. "
                f"Found {primary_count} imports."
            )
            confidence = min(0.7, 0.5 + primary_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in cb_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.circuit_breakers",
            category="resilience",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "circuit_breaker_library_counts": dict(cb_libs),
                "primary_library": primary,
                "circuit_breaker_count": circuit_breaker_count,
            },
        ))

    def _detect_health_checks(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect health check endpoint patterns."""
        health_endpoints: list[tuple[str, int, str]] = []
        health_functions: list[tuple[str, int, str]] = []
        has_readiness = False
        has_liveness = False

        # Health endpoint path patterns
        health_paths = re.compile(
            r"""['"]/(health|healthz|ready|readyz|live|livez|status|ping)['"]""",
            re.IGNORECASE,
        )
        readiness_paths = re.compile(r"""['"]/(ready|readyz|readiness)['"]""", re.IGNORECASE)
        liveness_paths = re.compile(r"""['"]/(live|livez|liveness|alive)['"]""", re.IGNORECASE)

        # Health function name patterns
        health_func_names = re.compile(
            r"^(health[_-]?check|healthcheck|check[_-]?health|readiness|liveness|ready|live|ping|status)$",
            re.IGNORECASE,
        )

        # Check for route decorators with health paths
        for rel_path, dec in index.get_all_decorators():
            # Look for FastAPI/Flask/Starlette route decorators
            if any(x in dec.name.lower() for x in ["get", "route", "api_route"]):
                # Check arguments for health paths
                dec_str = " ".join(dec.call_args) if dec.call_args else ""
                if health_paths.search(dec_str):
                    health_endpoints.append((rel_path, dec.line, dec_str))
                    if readiness_paths.search(dec_str):
                        has_readiness = True
                    if liveness_paths.search(dec_str):
                        has_liveness = True

        # Check file content for health endpoints
        for rel_path, file_idx in index.files.items():
            if file_idx.role in ("test", "docs"):
                continue

            for i, line in enumerate(file_idx.lines, 1):
                # Look for health paths in route definitions
                if health_paths.search(line):
                    # Avoid duplicates
                    if not any(rel_path == e[0] and abs(i - e[1]) < 3 for e in health_endpoints):
                        health_endpoints.append((rel_path, i, line.strip()))
                        if readiness_paths.search(line):
                            has_readiness = True
                        if liveness_paths.search(line):
                            has_liveness = True

        # Check for health-related function definitions
        for rel_path, func in index.get_all_functions():
            if health_func_names.match(func.name):
                health_functions.append((rel_path, func.line, func.name))
                func_lower = func.name.lower()
                if "ready" in func_lower or "readiness" in func_lower:
                    has_readiness = True
                if "live" in func_lower or "liveness" in func_lower or "alive" in func_lower:
                    has_liveness = True

        health_endpoint_count = len(health_endpoints)
        health_function_count = len(health_functions)

        if health_endpoint_count == 0 and health_function_count == 0:
            return

        # Build title and description
        parts = []
        if health_endpoint_count > 0:
            parts.append(f"{health_endpoint_count} health endpoint(s)")
        if has_readiness:
            parts.append("readiness check")
        if has_liveness:
            parts.append("liveness check")

        if health_endpoint_count > 0:
            title = "Health check endpoints"
            description = f"Implements health checks: {', '.join(parts)}."
            confidence = min(0.9, 0.6 + health_endpoint_count * 0.1)
        else:
            title = "Health check functions"
            description = f"Has {health_function_count} health-related function(s) but no clear endpoints."
            confidence = 0.5

        # Build evidence
        evidence = []
        for rel_path, line, _ in health_endpoints[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)
        for rel_path, line, _ in health_functions[:max(0, ctx.max_evidence_snippets - len(evidence))]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.health_checks",
            category="resilience",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "health_endpoint_count": health_endpoint_count,
                "health_function_count": health_function_count,
                "has_readiness": has_readiness,
                "has_liveness": has_liveness,
            },
        ))
