"""Python logging conventions detector."""

from __future__ import annotations

import ast
import re
from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from .index import make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class PythonLoggingConventionsDetector(PythonDetector):
    """Detect Python logging library and structured logging conventions."""

    name = "python_logging_conventions"
    description = "Detects logging library usage and structured logging patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect logging library usage and structured logging patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect logging library
        self._detect_logging_library(ctx, index, result)

        # Detect structured logging fields
        self._detect_structured_fields(ctx, index, result)

        return result

    def _detect_logging_library(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect which logging library is used."""
        library_counts: Counter[str] = Counter()
        library_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # Standard library logging
            if imp.module == "logging" or "logging" in imp.names:
                library_counts["stdlib_logging"] += 1
                if "stdlib_logging" not in library_examples:
                    library_examples["stdlib_logging"] = []
                library_examples["stdlib_logging"].append((rel_path, imp.line))

            # Structlog
            if "structlog" in imp.module or "structlog" in imp.names:
                library_counts["structlog"] += 1
                if "structlog" not in library_examples:
                    library_examples["structlog"] = []
                library_examples["structlog"].append((rel_path, imp.line))

            # Loguru
            if "loguru" in imp.module or "loguru" in imp.names:
                library_counts["loguru"] += 1
                if "loguru" not in library_examples:
                    library_examples["loguru"] = []
                library_examples["loguru"].append((rel_path, imp.line))

        # Also check for getLogger calls
        for rel_path, call in index.get_all_calls():
            if call.name == "logging.getLogger" or call.name == "getLogger":
                library_counts["stdlib_logging"] += 1
            elif call.name == "structlog.get_logger" or call.name.endswith("get_logger"):
                if "structlog" in call.name:
                    library_counts["structlog"] += 1
            elif call.name == "loguru.logger" or "loguru" in call.name:
                library_counts["loguru"] += 1

        if not library_counts:
            return

        # Determine primary library
        primary_lib, primary_count = library_counts.most_common(1)[0]
        total = sum(library_counts.values())
        primary_ratio = primary_count / total if total else 0

        # Map to friendly names
        lib_names = {
            "stdlib_logging": "Python standard logging",
            "structlog": "structlog",
            "loguru": "Loguru",
        }

        if len(library_counts) == 1:
            title = f"Uses {lib_names.get(primary_lib, primary_lib)}"
            description = (
                f"Exclusively uses {lib_names.get(primary_lib, primary_lib)} for logging. "
                f"Found {primary_count} usages."
            )
            confidence = min(0.95, 0.7 + primary_count * 0.02)
        else:
            other_libs = [lib_names.get(lib, lib) for lib in library_counts if lib != primary_lib]
            title = f"Primary logging: {lib_names.get(primary_lib, primary_lib)}"
            description = (
                f"Uses {lib_names.get(primary_lib, primary_lib)} as primary logging library "
                f"({primary_count}/{total} usages). Also uses: {', '.join(other_libs)}."
            )
            confidence = min(0.8, 0.5 + primary_ratio * 0.3)

        # Build evidence
        evidence = []
        for rel_path, line in library_examples.get(primary_lib, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.logging_library",
            category="logging",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "library_counts": dict(library_counts),
                "primary_library": primary_lib,
                "primary_ratio": round(primary_ratio, 3),
            },
        ))

    def _detect_structured_fields(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect common structured logging fields."""
        # We need to look at actual call arguments to find common fields
        # This requires more detailed AST analysis

        field_counter: Counter[str] = Counter()
        field_examples: list[tuple[str, int, list[str]]] = []

        # Common fields we're looking for
        common_fields = {
            "user_id", "request_id", "trace_id", "correlation_id",
            "session_id", "order_id", "customer_id", "transaction_id",
            "action", "event", "status", "duration", "error", "exception",
            "method", "path", "url", "ip", "user_agent",
        }

        # Look through calls for logging patterns
        for rel_path, call in index.get_all_calls():
            # Check for structlog bind() or new()
            if call.name.endswith(".bind") or call.name.endswith(".new"):
                if call.kwargs:
                    for kw in call.kwargs:
                        field_counter[kw] += 1
                    field_examples.append((rel_path, call.line, call.kwargs))

            # Check for logging with extra={}
            if any(x in call.name for x in ["logger.", "logging.", ".info", ".error", ".warning", ".debug"]):
                if "extra" in call.kwargs:
                    # Mark that extra is used
                    field_counter["__extra_used__"] += 1

        # Also look for extra dict keys by scanning source (heuristic)
        extra_fields: Counter[str] = Counter()
        for rel_path, file_idx in index.files.items():
            if file_idx.role == "test":
                continue
            content = "\n".join(file_idx.lines)
            # Look for extra={...} patterns
            extra_matches = re.findall(r'extra\s*=\s*\{([^}]+)\}', content)
            for match in extra_matches:
                # Extract keys from the dict literal
                keys = re.findall(r'["\'](\w+)["\']:', match)
                for key in keys:
                    extra_fields[key] += 1
                    field_counter[key] += 1

        # Combine field counts
        all_fields = field_counter

        if len(all_fields) < 3:
            return

        # Remove internal markers
        all_fields.pop("__extra_used__", None)

        if not all_fields:
            return

        # Find top fields
        top_fields = all_fields.most_common(10)
        total_field_uses = sum(all_fields.values())

        # Check for common patterns
        has_request_id = any("request" in f[0] or "trace" in f[0] or "correlation" in f[0] for f in top_fields)
        has_user_id = any("user" in f[0] for f in top_fields)

        field_list = [f[0] for f in top_fields[:5]]

        if has_request_id:
            title = "Structured logging with request/trace IDs"
            description = (
                f"Structured logging includes request correlation fields. "
                f"Common fields: {', '.join(field_list)}."
            )
            confidence = 0.8
        else:
            title = "Structured logging with custom fields"
            description = (
                f"Uses structured logging with custom fields. "
                f"Common fields: {', '.join(field_list)}."
            )
            confidence = 0.7

        # Build evidence
        evidence = []
        for rel_path, line, fields in field_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.logging_fields",
            category="logging",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "top_fields": dict(top_fields),
                "total_field_uses": total_field_uses,
                "has_request_correlation": has_request_id,
            },
        ))
