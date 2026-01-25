"""Python resource management patterns detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonResourceManagementDetector(PythonDetector):
    """Detect Python resource management patterns."""

    name = "python_resource_management"
    description = "Detects context manager usage and resource handling patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect resource management patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_context_manager_usage(ctx, index, result)

        return result

    def _detect_context_manager_usage(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect context manager usage patterns."""
        context_types: Counter[str] = Counter()
        context_examples: dict[str, list[tuple[str, int]]] = {}
        async_count = 0
        sync_count = 0

        for rel_path, with_stmt in index.get_all_with_statements():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # Categorize the context manager
            category = self._categorize_context_manager(with_stmt.context_expr)
            if category:
                context_types[category] += 1
                if category not in context_examples:
                    context_examples[category] = []
                if len(context_examples[category]) < 5:
                    context_examples[category].append((rel_path, with_stmt.line))

            if with_stmt.is_async:
                async_count += 1
            else:
                sync_count += 1

        total = sync_count + async_count
        if total < 3:
            return  # Not enough evidence

        # Report overall context manager usage
        title = "Context manager usage"
        if async_count > 0 and sync_count > 0:
            description = (
                f"Uses context managers for resource management. "
                f"{total} with statements ({sync_count} sync, {async_count} async)."
            )
        elif async_count > 0:
            description = f"Uses async context managers. {async_count} async with statements."
        else:
            description = f"Uses context managers for resource management. {sync_count} with statements."

        # Add breakdown by type
        if context_types:
            type_summary = ", ".join(
                f"{cat} ({count})"
                for cat, count in context_types.most_common(3)
            )
            description += f" Types: {type_summary}."

        # Build evidence from most common type
        evidence = []
        if context_types:
            top_category = context_types.most_common(1)[0][0]
            for rel_path, line in context_examples.get(top_category, [])[:ctx.max_evidence_snippets]:
                ev = make_evidence(index, rel_path, line, radius=3)
                if ev:
                    evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.context_managers",
            category="resource_management",
            title=title,
            description=description,
            confidence=min(0.9, 0.6 + total * 0.02),
            language="python",
            evidence=evidence,
            stats={
                "total_with_statements": total,
                "sync_count": sync_count,
                "async_count": async_count,
                "context_types": dict(context_types.most_common(10)),
            },
        ))

        # Report specific resource patterns
        for category, count in context_types.most_common(5):
            if count < 3:
                continue

            cat_title, cat_desc = self._get_category_info(category, count)

            # Build evidence
            cat_evidence = []
            for rel_path, line in context_examples.get(category, [])[:ctx.max_evidence_snippets]:
                ev = make_evidence(index, rel_path, line, radius=3)
                if ev:
                    cat_evidence.append(ev)

            result.rules.append(self.make_rule(
                rule_id=f"python.conventions.context_{category}",
                category="resource_management",
                title=cat_title,
                description=cat_desc,
                confidence=min(0.85, 0.5 + count * 0.05),
                language="python",
                evidence=cat_evidence,
                stats={
                    "usage_count": count,
                    "category": category,
                },
            ))

    def _categorize_context_manager(self, context_expr: str) -> str | None:
        """Categorize a context manager by its expression."""
        expr_lower = context_expr.lower()

        # File handling
        if "open" in expr_lower or "file" in expr_lower:
            return "file_io"

        # Database/sessions
        if any(db in expr_lower for db in ["session", "connection", "transaction", "cursor"]):
            return "database"

        # HTTP clients
        if any(http in expr_lower for http in ["client", "httpx", "aiohttp", "requests"]):
            return "http_client"

        # Locks and threading
        if any(lock in expr_lower for lock in ["lock", "semaphore", "condition", "event"]):
            return "threading"

        # Temporary resources
        if any(temp in expr_lower for temp in ["tempfile", "temporary", "tempdir"]):
            return "temporary"

        # Mocking (in tests)
        if any(mock in expr_lower for mock in ["mock", "patch", "monkeypatch"]):
            return "mocking"

        # Timing/profiling
        if any(time in expr_lower for time in ["timer", "stopwatch", "profile"]):
            return "timing"

        # Suppress exceptions
        if "suppress" in expr_lower:
            return "exception_handling"

        # Redirect stdout/stderr
        if "redirect" in expr_lower:
            return "io_redirect"

        return None

    def _get_category_info(self, category: str, count: int) -> tuple[str, str]:
        """Get title and description for a context manager category."""
        info = {
            "file_io": (
                "File I/O with context managers",
                f"Uses context managers for file operations. {count} usages ensure proper file cleanup.",
            ),
            "database": (
                "Database sessions with context managers",
                f"Uses context managers for database connections/sessions. {count} usages.",
            ),
            "http_client": (
                "HTTP clients with context managers",
                f"Uses context managers for HTTP client lifecycle. {count} usages.",
            ),
            "threading": (
                "Thread synchronization with context managers",
                f"Uses context managers for locks/synchronization. {count} usages.",
            ),
            "temporary": (
                "Temporary files with context managers",
                f"Uses context managers for temporary files/directories. {count} usages.",
            ),
            "mocking": (
                "Test mocking with context managers",
                f"Uses context managers for test mocking. {count} usages.",
            ),
            "timing": (
                "Timing/profiling with context managers",
                f"Uses context managers for timing/profiling. {count} usages.",
            ),
            "exception_handling": (
                "Exception suppression with context managers",
                f"Uses contextlib.suppress for exception handling. {count} usages.",
            ),
            "io_redirect": (
                "I/O redirection with context managers",
                f"Uses context managers for I/O redirection. {count} usages.",
            ),
        }
        return info.get(category, (f"{category} context managers", f"{count} usages."))
