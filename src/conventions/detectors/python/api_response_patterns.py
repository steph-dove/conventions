"""Python API response patterns detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonAPIResponsePatternsDetector(PythonDetector):
    """Detect Python API response patterns."""

    name = "python_api_response_patterns"
    description = "Detects API response envelope patterns and pagination styles"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect API response patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_response_envelope(ctx, index, result)
        self._detect_pagination_pattern(ctx, index, result)

        return result

    def _detect_response_envelope(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect API response envelope patterns."""
        # First, check if this is an API/web application (not a client library)
        # by looking for web framework imports
        has_web_framework = False
        for rel_path, imp in index.get_all_imports():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue
            # Check for web frameworks that define API endpoints
            if any(fw in imp.module for fw in ["fastapi", "flask", "django", "starlette", "sanic", "aiohttp.web"]):
                has_web_framework = True
                break
            if any(fw in imp.names for fw in ["FastAPI", "Flask", "APIRouter"]):
                has_web_framework = True
                break

        # Skip detection for client libraries (no web framework found)
        if not has_web_framework:
            return

        # Look for response model classes
        envelope_indicators: Counter[str] = Counter()
        envelope_examples: list[tuple[str, int, str]] = []

        for rel_path, cls in index.get_all_classes():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            cls_lower = cls.name.lower()

            # Check for envelope-style response classes
            if any(pattern in cls_lower for pattern in ["response", "result", "envelope", "wrapper"]):
                # Check if it has envelope-like structure based on name
                if any(field in cls_lower for field in ["api", "json", "data"]):
                    envelope_indicators["envelope_class"] += 1
                    if len(envelope_examples) < 5:
                        envelope_examples.append((rel_path, cls.line, cls.name))

        # Look for common envelope field patterns in function returns/calls
        envelope_fields = {
            "data": 0,
            "meta": 0,
            "error": 0,
            "errors": 0,
            "message": 0,
            "status": 0,
            "success": 0,
            "result": 0,
            "items": 0,
            "payload": 0,
        }

        for rel_path, call in index.get_all_calls():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # Check kwargs for envelope field names
            for kwarg in call.kwargs:
                if kwarg.lower() in envelope_fields:
                    envelope_fields[kwarg.lower()] += 1

        # Analyze patterns
        has_data_field = envelope_fields["data"] >= 3 or envelope_fields["result"] >= 3
        has_meta_field = envelope_fields["meta"] >= 2
        has_error_field = envelope_fields["error"] >= 2 or envelope_fields["errors"] >= 2
        has_status_field = envelope_fields["status"] >= 2 or envelope_fields["success"] >= 2

        envelope_score = sum([has_data_field, has_meta_field, has_error_field, has_status_field])

        if envelope_score < 2 and envelope_indicators["envelope_class"] < 2:
            return  # Not enough evidence of envelope pattern

        if envelope_score >= 3:
            title = "API response envelope pattern"
            description = "Uses consistent response envelope structure with "
            parts = []
            if has_data_field:
                parts.append("data")
            if has_meta_field:
                parts.append("meta")
            if has_error_field:
                parts.append("errors")
            if has_status_field:
                parts.append("status")
            description += ", ".join(parts) + " fields."
            pattern = "full_envelope"
            confidence = 0.85
        elif has_data_field:
            title = "Data wrapper response pattern"
            description = "Wraps API responses in a 'data' field."
            pattern = "data_wrapper"
            confidence = 0.75
        else:
            title = "Response envelope classes"
            description = f"Uses response envelope classes ({envelope_indicators['envelope_class']} found)."
            pattern = "class_based"
            confidence = 0.7

        # Build evidence
        evidence = []
        for rel_path, line, name in envelope_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.response_envelope",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "envelope_classes": envelope_indicators["envelope_class"],
                "field_counts": {k: v for k, v in envelope_fields.items() if v > 0},
                "pattern": pattern,
            },
        ))

    def _detect_pagination_pattern(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect pagination patterns."""
        offset_count = 0
        cursor_count = 0
        page_count = 0
        pagination_examples: list[tuple[str, int]] = []

        # Check function parameters and calls for pagination indicators
        for rel_path, func in index.get_all_functions():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # We can't easily check function params from FunctionInfo
            # But we can check function names
            func_lower = func.name.lower()
            if "paginate" in func_lower or "pagination" in func_lower:
                if len(pagination_examples) < 5:
                    pagination_examples.append((rel_path, func.line))

        # Check calls for pagination parameters
        for rel_path, call in index.get_all_calls():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            kwargs_lower = [k.lower() for k in call.kwargs]

            if "offset" in kwargs_lower or "skip" in kwargs_lower:
                offset_count += 1
            if "cursor" in kwargs_lower or "after" in kwargs_lower or "before" in kwargs_lower:
                cursor_count += 1
            if "page" in kwargs_lower or "page_number" in kwargs_lower:
                page_count += 1
            if "limit" in kwargs_lower or "page_size" in kwargs_lower:
                pass  # Both patterns use limit

        total = offset_count + cursor_count + page_count
        if total < 3:
            return

        if cursor_count > offset_count and cursor_count > page_count:
            title = "Cursor-based pagination"
            description = f"Uses cursor-based pagination. {cursor_count} cursor/after/before usages."
            pattern = "cursor"
            confidence = 0.8
        elif offset_count > page_count:
            title = "Offset-based pagination"
            description = f"Uses offset/skip pagination. {offset_count} offset/skip usages."
            pattern = "offset"
            confidence = 0.8
        elif page_count > 0:
            title = "Page number pagination"
            description = f"Uses page number pagination. {page_count} page/page_number usages."
            pattern = "page"
            confidence = 0.8
        else:
            return

        # Build evidence
        evidence = []
        for rel_path, line in pagination_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.pagination_pattern",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "offset_count": offset_count,
                "cursor_count": cursor_count,
                "page_count": page_count,
                "pattern": pattern,
            },
        ))
