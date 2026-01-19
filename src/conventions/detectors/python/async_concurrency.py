"""Python async and concurrency conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from .index import make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class PythonAsyncConventionsDetector(PythonDetector):
    """Detect Python async/concurrency conventions."""

    name = "python_async_conventions"
    description = "Detects async style and background job patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect async style and background job patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect async style
        self._detect_async_style(ctx, index, result)

        # Detect background jobs
        self._detect_background_jobs(ctx, index, result)

        return result

    def _detect_async_style(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect async vs sync function ratio."""
        async_count = 0
        sync_count = 0
        async_examples: list[tuple[str, int, str]] = []
        sync_examples: list[tuple[str, int, str]] = []

        # Focus on API modules for style detection
        api_files = index.get_files_by_role("api")

        for file_idx in api_files:
            rel_path = file_idx.relative_path

            for func in file_idx.functions:
                if func.is_async:
                    async_count += 1
                    if len(async_examples) < 5:
                        async_examples.append((rel_path, func.line, func.name))
                else:
                    # Skip dunder methods and private methods
                    if not func.name.startswith("_"):
                        sync_count += 1
                        if len(sync_examples) < 5:
                            sync_examples.append((rel_path, func.line, func.name))

        total = async_count + sync_count
        if total < 3:
            return

        async_ratio = async_count / total if total else 0

        if async_ratio >= 0.8:
            title = "Async-first API design"
            description = (
                f"API endpoints are predominantly async. "
                f"{async_count}/{total} endpoint functions are async."
            )
            confidence = min(0.9, 0.6 + async_ratio * 0.3)
        elif async_ratio >= 0.4:
            title = "Mixed async/sync API design"
            description = (
                f"API uses both async and sync endpoints. "
                f"Async: {async_count}, Sync: {sync_count}."
            )
            confidence = 0.7
        else:
            title = "Sync-first API design"
            description = (
                f"API endpoints are predominantly synchronous. "
                f"Only {async_count}/{total} functions are async."
            )
            confidence = min(0.9, 0.6 + (1 - async_ratio) * 0.3)

        # Check for asyncio patterns
        asyncio_patterns = 0
        asyncio_examples: list[tuple[str, int]] = []

        for rel_path, call in index.get_all_calls():
            if any(x in call.name for x in [
                "asyncio.gather", "asyncio.create_task", "asyncio.wait",
                "gather", "create_task"
            ]):
                asyncio_patterns += 1
                if len(asyncio_examples) < 5:
                    asyncio_examples.append((rel_path, call.line))

        if asyncio_patterns > 0:
            description += f" Uses asyncio concurrency patterns ({asyncio_patterns} usages)."

        # Build evidence
        evidence = []
        for rel_path, line, name in async_examples[:2]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)
        for rel_path, line, name in sync_examples[:2]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.async_style",
            category="concurrency",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence[:ctx.max_evidence_snippets],
            stats={
                "async_count": async_count,
                "sync_count": sync_count,
                "async_ratio": round(async_ratio, 3),
                "asyncio_patterns": asyncio_patterns,
            },
        ))

    def _detect_background_jobs(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect background job framework usage."""
        job_libs: Counter[str] = Counter()
        job_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # Celery
            if "celery" in imp.module or "Celery" in imp.names:
                job_libs["celery"] += 1
                if "celery" not in job_examples:
                    job_examples["celery"] = []
                job_examples["celery"].append((rel_path, imp.line))

            # RQ (Redis Queue)
            if imp.module == "rq" or "rq" in imp.names:
                job_libs["rq"] += 1
                if "rq" not in job_examples:
                    job_examples["rq"] = []
                job_examples["rq"].append((rel_path, imp.line))

            # Dramatiq
            if "dramatiq" in imp.module:
                job_libs["dramatiq"] += 1
                if "dramatiq" not in job_examples:
                    job_examples["dramatiq"] = []
                job_examples["dramatiq"].append((rel_path, imp.line))

            # Huey
            if "huey" in imp.module:
                job_libs["huey"] += 1
                if "huey" not in job_examples:
                    job_examples["huey"] = []
                job_examples["huey"].append((rel_path, imp.line))

            # APScheduler
            if "apscheduler" in imp.module:
                job_libs["apscheduler"] += 1
                if "apscheduler" not in job_examples:
                    job_examples["apscheduler"] = []
                job_examples["apscheduler"].append((rel_path, imp.line))

            # arq
            if imp.module == "arq":
                job_libs["arq"] += 1
                if "arq" not in job_examples:
                    job_examples["arq"] = []
                job_examples["arq"].append((rel_path, imp.line))

            # BackgroundTasks (FastAPI)
            if "BackgroundTasks" in imp.names:
                job_libs["fastapi_background"] += 1
                if "fastapi_background" not in job_examples:
                    job_examples["fastapi_background"] = []
                job_examples["fastapi_background"].append((rel_path, imp.line))

        # Check for task decorators
        task_decorators = 0
        for rel_path, dec in index.get_all_decorators():
            if any(x in dec.name for x in [".task", "shared_task", "celery.task"]):
                task_decorators += 1
                job_libs["celery"] = job_libs.get("celery", 0) + 1

        if not job_libs:
            return

        primary, primary_count = job_libs.most_common(1)[0]
        total = sum(job_libs.values())

        lib_names = {
            "celery": "Celery",
            "rq": "RQ (Redis Queue)",
            "dramatiq": "Dramatiq",
            "huey": "Huey",
            "apscheduler": "APScheduler",
            "arq": "arq",
            "fastapi_background": "FastAPI BackgroundTasks",
        }

        if len(job_libs) == 1:
            title = f"Background jobs with {lib_names.get(primary, primary)}"
            description = (
                f"Uses {lib_names.get(primary, primary)} for background task processing. "
                f"Found {primary_count} usages."
            )
            confidence = min(0.9, 0.6 + primary_count * 0.03)
        else:
            other_libs = [lib_names.get(lib, lib) for lib in job_libs if lib != primary]
            title = f"Primary job queue: {lib_names.get(primary, primary)}"
            description = (
                f"Uses {lib_names.get(primary, primary)} ({primary_count}/{total}). "
                f"Also uses: {', '.join(other_libs)}."
            )
            confidence = min(0.8, 0.5 + total * 0.03)

        # Build evidence
        evidence = []
        for rel_path, line in job_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.background_jobs",
            category="concurrency",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "job_library_counts": dict(job_libs),
                "primary_library": primary,
                "task_decorators": task_decorators,
            },
        ))
