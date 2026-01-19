"""Python error handling conventions detector."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from ..base import DetectorContext, DetectorResult, PythonDetector
from .index import make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class PythonErrorConventionsDetector(PythonDetector):
    """Detect Python error handling conventions."""

    name = "python_error_conventions"
    description = "Detects error handling patterns, custom exceptions, and error boundaries"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect error handling patterns, custom exceptions, and error boundaries."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect HTTPException usage by module role
        self._detect_http_exception_boundary(ctx, index, result)

        # Detect custom exception taxonomy
        self._detect_exception_taxonomy(ctx, index, result)

        # Detect exception handler patterns
        self._detect_exception_handlers(ctx, index, result)

        return result

    def _detect_http_exception_boundary(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect where HTTPException is raised (boundary consistency)."""
        # Find HTTPException calls by role
        http_exception_by_role: Counter[str] = Counter()
        http_exception_examples: list[tuple[str, int]] = []

        for rel_path, call in index.get_all_calls():
            if "HTTPException" in call.name:
                file_idx = index.files.get(rel_path)
                if file_idx:
                    http_exception_by_role[file_idx.role] += 1
                    if len(http_exception_examples) < 10:
                        http_exception_examples.append((rel_path, call.line))

        total_http_exceptions = sum(http_exception_by_role.values())

        if total_http_exceptions < 3:
            return  # Not enough evidence

        # Determine boundary pattern
        api_count = http_exception_by_role.get("api", 0)
        service_count = http_exception_by_role.get("service", 0)
        other_count = total_http_exceptions - api_count - service_count

        api_ratio = api_count / total_http_exceptions if total_http_exceptions else 0

        if api_ratio >= 0.8:
            title = "HTTP errors raised at API boundary"
            description = (
                f"HTTPException is consistently raised in API layer. "
                f"{api_count}/{total_http_exceptions} occurrences are in API modules."
            )
            confidence = min(0.9, 0.6 + api_ratio * 0.3)
        elif api_ratio >= 0.5:
            title = "Mixed HTTP error boundary"
            description = (
                f"HTTPException is raised in multiple layers. "
                f"API: {api_count}, Service: {service_count}, Other: {other_count}."
            )
            confidence = 0.6
        else:
            title = "HTTP errors raised in service layer"
            description = (
                f"HTTPException is frequently raised outside the API layer. "
                f"Service: {service_count}, API: {api_count}, Other: {other_count}."
            )
            confidence = 0.7

        # Build evidence
        evidence = []
        for rel_path, line in http_exception_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.error_handling_boundary",
            category="error_handling",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "total_http_exceptions": total_http_exceptions,
                "by_role": dict(http_exception_by_role),
                "api_ratio": round(api_ratio, 3),
            },
        ))

    def _detect_exception_taxonomy(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect custom exception classes and their naming patterns."""
        custom_exceptions: list[tuple[str, str, int, list[str]]] = []  # (path, name, line, bases)

        for rel_path, cls in index.get_all_classes():
            # Check if it inherits from Exception or Error
            exception_bases = [
                b for b in cls.bases
                if any(exc_name in b for exc_name in ("Exception", "Error", "BaseException"))
            ]
            if exception_bases:
                custom_exceptions.append((rel_path, cls.name, cls.line, cls.bases))

        if len(custom_exceptions) < 2:
            return  # Not enough evidence

        # Analyze naming patterns
        error_suffix_count = sum(1 for _, name, _, _ in custom_exceptions if name.endswith("Error"))
        exception_suffix_count = sum(1 for _, name, _, _ in custom_exceptions if name.endswith("Exception"))

        total = len(custom_exceptions)

        # Determine dominant pattern
        if error_suffix_count > exception_suffix_count:
            dominant_suffix = "Error"
            dominant_count = error_suffix_count
        else:
            dominant_suffix = "Exception"
            dominant_count = exception_suffix_count

        consistency = dominant_count / total if total else 0

        if consistency >= 0.8:
            title = f"Consistent *{dominant_suffix} naming convention"
            description = (
                f"Custom exceptions follow {dominant_suffix} suffix pattern. "
                f"{dominant_count}/{total} exceptions use this pattern."
            )
            confidence = min(0.9, 0.6 + consistency * 0.3)
        elif consistency >= 0.5:
            title = "Mixed exception naming conventions"
            description = (
                f"Exception naming is mixed: {error_suffix_count} *Error, "
                f"{exception_suffix_count} *Exception out of {total} total."
            )
            confidence = 0.6
        else:
            title = "Varied exception naming patterns"
            description = (
                f"Exception naming varies across {total} custom exceptions."
            )
            confidence = 0.5

        # Build evidence
        evidence = []
        for rel_path, name, line, bases in custom_exceptions[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        # List exception names
        exception_names = [name for _, name, _, _ in custom_exceptions]

        result.rules.append(self.make_rule(
            rule_id="python.conventions.error_taxonomy",
            category="error_handling",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "total_custom_exceptions": total,
                "error_suffix_count": error_suffix_count,
                "exception_suffix_count": exception_suffix_count,
                "exception_names": exception_names[:20],
                "consistency": round(consistency, 3),
            },
        ))

    def _detect_exception_handlers(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect centralized exception handler patterns."""
        # Look for exception handler decorators and calls
        exception_handler_decorators = []
        exception_handler_calls = []

        for rel_path, dec in index.get_all_decorators():
            if "exception_handler" in dec.name.lower():
                exception_handler_decorators.append((rel_path, dec.line, dec.name))

        for rel_path, call in index.get_all_calls():
            if "add_exception_handler" in call.name or "exception_handler" in call.name.lower():
                exception_handler_calls.append((rel_path, call.line, call.name))

        total_handlers = len(exception_handler_decorators) + len(exception_handler_calls)

        if total_handlers < 2:
            return

        # Determine if centralized or distributed
        handler_files = set()
        for rel_path, _, _ in exception_handler_decorators + exception_handler_calls:
            handler_files.add(rel_path)

        if len(handler_files) == 1:
            title = "Centralized exception handling"
            description = (
                f"Exception handlers are centralized in a single module. "
                f"Found {total_handlers} handlers in {list(handler_files)[0]}."
            )
            confidence = 0.85
        elif len(handler_files) <= 3:
            title = "Semi-centralized exception handling"
            description = (
                f"Exception handlers are spread across {len(handler_files)} modules. "
                f"Total handlers: {total_handlers}."
            )
            confidence = 0.7
        else:
            title = "Distributed exception handling"
            description = (
                f"Exception handlers are spread across {len(handler_files)} modules."
            )
            confidence = 0.6

        # Build evidence
        evidence = []
        for rel_path, line, name in (exception_handler_decorators + exception_handler_calls)[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.exception_handlers",
            category="error_handling",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "total_handlers": total_handlers,
                "decorator_handlers": len(exception_handler_decorators),
                "call_handlers": len(exception_handler_calls),
                "handler_files": list(handler_files),
            },
        ))
