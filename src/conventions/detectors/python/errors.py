"""Python error handling conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


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

        # Detect custom error wrapper patterns
        self._detect_error_wrapper_patterns(ctx, index, result)

        # Detect exception chaining patterns
        self._detect_exception_chaining(ctx, index, result)

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

    def _detect_error_wrapper_patterns(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect custom error wrapper/abstraction patterns.

        This looks for patterns like:
        - A common function called in many except handlers (error wrapper)
        - A custom exception raised in many except handlers (error transformation)
        - A function consistently returned from except handlers (error response)
        """
        # Collect statistics from all except handlers
        calls_in_handlers: Counter[str] = Counter()
        raises_in_handlers: Counter[str] = Counter()
        return_calls: Counter[str] = Counter()
        handler_examples: dict[str, list[tuple[str, int]]] = {}

        total_handlers = 0

        for rel_path, handler in index.get_all_except_handlers():
            # Skip test files
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            total_handlers += 1

            # Count function calls in handlers
            for call in handler.calls_in_handler:
                # Skip common logging calls and re-raises
                if any(skip in call.lower() for skip in ["log", "print", "raise", "logger"]):
                    continue
                calls_in_handlers[call] += 1
                if call not in handler_examples:
                    handler_examples[call] = []
                if len(handler_examples[call]) < 5:
                    handler_examples[call].append((rel_path, handler.line))

            # Count exceptions raised in handlers
            for raise_name in handler.raises_in_handler:
                raises_in_handlers[raise_name] += 1
                key = f"raise:{raise_name}"
                if key not in handler_examples:
                    handler_examples[key] = []
                if len(handler_examples[key]) < 5:
                    handler_examples[key].append((rel_path, handler.line))

            # Count return calls
            if handler.returns_call:
                return_calls[handler.returns_call] += 1
                key = f"return:{handler.returns_call}"
                if key not in handler_examples:
                    handler_examples[key] = []
                if len(handler_examples[key]) < 5:
                    handler_examples[key].append((rel_path, handler.line))

        if total_handlers < 5:
            return  # Not enough handlers to detect patterns

        # Find significant patterns (used in at least 20% of handlers or 5+ times)
        min_threshold = max(3, int(total_handlers * 0.15))

        # Detect error wrapper functions
        wrapper_functions = [
            (func, count) for func, count in calls_in_handlers.most_common(5)
            if count >= min_threshold
        ]

        # Detect error transformation (custom exceptions raised)
        error_transformations = [
            (exc, count) for exc, count in raises_in_handlers.most_common(5)
            if count >= min_threshold and exc not in ("Exception", "RuntimeError", "ValueError")
        ]

        # Detect error response patterns
        response_patterns = [
            (func, count) for func, count in return_calls.most_common(3)
            if count >= min_threshold
        ]

        # Generate rules for detected patterns
        if wrapper_functions:
            top_wrapper, top_count = wrapper_functions[0]
            usage_ratio = top_count / total_handlers

            title = f"Error wrapper pattern: {top_wrapper}"
            description = (
                f"Uses '{top_wrapper}' as a common error handler function. "
                f"Called in {top_count}/{total_handlers} ({usage_ratio:.0%}) except blocks."
            )
            if len(wrapper_functions) > 1:
                others = ", ".join(f[0] for f in wrapper_functions[1:3])
                description += f" Also uses: {others}."

            confidence = min(0.9, 0.5 + usage_ratio * 0.4)

            evidence = []
            for rel_path, line in handler_examples.get(top_wrapper, [])[:ctx.max_evidence_snippets]:
                ev = make_evidence(index, rel_path, line, radius=5)
                if ev:
                    evidence.append(ev)

            result.rules.append(self.make_rule(
                rule_id="python.conventions.error_wrapper",
                category="error_handling",
                title=title,
                description=description,
                confidence=confidence,
                language="python",
                evidence=evidence,
                stats={
                    "wrapper_function": top_wrapper,
                    "usage_count": top_count,
                    "total_handlers": total_handlers,
                    "usage_ratio": round(usage_ratio, 3),
                    "other_wrappers": [f[0] for f in wrapper_functions[1:]],
                },
            ))

        if error_transformations:
            top_exc, top_count = error_transformations[0]
            usage_ratio = top_count / total_handlers

            title = f"Error transformation: {top_exc}"
            description = (
                f"Transforms caught exceptions to '{top_exc}'. "
                f"Raised in {top_count}/{total_handlers} ({usage_ratio:.0%}) except blocks."
            )

            confidence = min(0.85, 0.5 + usage_ratio * 0.35)

            evidence = []
            for rel_path, line in handler_examples.get(f"raise:{top_exc}", [])[:ctx.max_evidence_snippets]:
                ev = make_evidence(index, rel_path, line, radius=5)
                if ev:
                    evidence.append(ev)

            result.rules.append(self.make_rule(
                rule_id="python.conventions.error_transformation",
                category="error_handling",
                title=title,
                description=description,
                confidence=confidence,
                language="python",
                evidence=evidence,
                stats={
                    "target_exception": top_exc,
                    "usage_count": top_count,
                    "total_handlers": total_handlers,
                    "usage_ratio": round(usage_ratio, 3),
                    "other_transforms": [e[0] for e in error_transformations[1:]],
                },
            ))

        if response_patterns:
            top_response, top_count = response_patterns[0]
            usage_ratio = top_count / total_handlers

            title = f"Standardized error response: {top_response}"
            description = (
                f"Uses '{top_response}' to generate standardized error responses. "
                f"Returned in {top_count}/{total_handlers} ({usage_ratio:.0%}) except blocks."
            )

            confidence = min(0.85, 0.5 + usage_ratio * 0.35)

            evidence = []
            for rel_path, line in handler_examples.get(f"return:{top_response}", [])[:ctx.max_evidence_snippets]:
                ev = make_evidence(index, rel_path, line, radius=5)
                if ev:
                    evidence.append(ev)

            result.rules.append(self.make_rule(
                rule_id="python.conventions.error_response_pattern",
                category="error_handling",
                title=title,
                description=description,
                confidence=confidence,
                language="python",
                evidence=evidence,
                stats={
                    "response_function": top_response,
                    "usage_count": top_count,
                    "total_handlers": total_handlers,
                    "usage_ratio": round(usage_ratio, 3),
                },
            ))

    def _detect_exception_chaining(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect exception chaining patterns (raise X from Y vs bare raise X)."""
        chained_raises = 0
        unchained_raises = 0
        bare_raises = 0
        chained_examples: list[tuple[str, int]] = []
        unchained_examples: list[tuple[str, int]] = []

        for rel_path, raise_info in index.get_all_raises():
            # Skip test files
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            if raise_info.is_bare_raise:
                bare_raises += 1
                continue

            if raise_info.has_from_clause:
                chained_raises += 1
                if len(chained_examples) < 10:
                    chained_examples.append((rel_path, raise_info.line))
            else:
                unchained_raises += 1
                if len(unchained_examples) < 10:
                    unchained_examples.append((rel_path, raise_info.line))

        total_non_bare = chained_raises + unchained_raises

        if total_non_bare < 3:
            return  # Not enough evidence

        chaining_ratio = chained_raises / total_non_bare if total_non_bare else 0

        # Determine pattern
        if chaining_ratio >= 0.8:
            title = "Excellent exception chaining"
            description = (
                f"Consistently uses 'raise X from Y' for exception chaining. "
                f"{chained_raises}/{total_non_bare} ({chaining_ratio:.0%}) raises use chaining."
            )
            confidence = 0.9
        elif chaining_ratio >= 0.6:
            title = "Good exception chaining"
            description = (
                f"Often uses 'raise X from Y' for exception chaining. "
                f"{chained_raises}/{total_non_bare} ({chaining_ratio:.0%}) raises use chaining."
            )
            confidence = 0.8
        elif chaining_ratio >= 0.4:
            title = "Partial exception chaining"
            description = (
                f"Sometimes uses 'raise X from Y'. "
                f"{chained_raises}/{total_non_bare} ({chaining_ratio:.0%}) raises use chaining. "
                f"Consider using 'raise X from Y' or 'raise X from None' for all transformations."
            )
            confidence = 0.7
        else:
            title = "Limited exception chaining"
            description = (
                f"Rarely uses 'raise X from Y'. "
                f"{chained_raises}/{total_non_bare} ({chaining_ratio:.0%}) raises use chaining. "
                f"Use 'raise X from Y' to preserve context or 'raise X from None' to suppress."
            )
            confidence = 0.7

        # Build evidence - show both chained and unchained examples
        evidence = []
        for rel_path, line in chained_examples[:2]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)
        for rel_path, line in unchained_examples[:2]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.exception_chaining",
            category="error_handling",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence[:ctx.max_evidence_snippets],
            stats={
                "chained_raises": chained_raises,
                "unchained_raises": unchained_raises,
                "bare_raises": bare_raises,
                "chaining_ratio": round(chaining_ratio, 3),
            },
        ))
