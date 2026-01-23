"""Python background task patterns detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonBackgroundTaskDetector(PythonDetector):
    """Detect Python background task patterns."""

    name = "python_background_tasks"
    description = "Detects Python background task libraries (Celery, RQ, Dramatiq)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Python background task patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        libraries: dict[str, dict] = {}
        examples: dict[str, list[tuple[str, int]]] = {}

        # Celery
        celery_imports = index.find_imports_matching("celery", limit=30)
        if celery_imports:
            libraries["celery"] = {
                "name": "Celery",
                "import_count": len(celery_imports),
            }
            examples["celery"] = [(f.file_path, f.line) for f in celery_imports[:5]]

        # RQ (Redis Queue)
        rq_imports = index.find_imports_matching("rq", limit=20)
        # Filter out false positives
        rq_imports = [i for i in rq_imports if i.module in ("rq", "rq.job", "rq.queue", "rq.worker")]
        if rq_imports:
            libraries["rq"] = {
                "name": "RQ (Redis Queue)",
                "import_count": len(rq_imports),
            }
            examples["rq"] = [(f.file_path, f.line) for f in rq_imports[:5]]

        # Dramatiq
        dramatiq_imports = index.find_imports_matching("dramatiq", limit=20)
        if dramatiq_imports:
            libraries["dramatiq"] = {
                "name": "Dramatiq",
                "import_count": len(dramatiq_imports),
            }
            examples["dramatiq"] = [(f.file_path, f.line) for f in dramatiq_imports[:5]]

        # Huey
        huey_imports = index.find_imports_matching("huey", limit=20)
        if huey_imports:
            libraries["huey"] = {
                "name": "Huey",
                "import_count": len(huey_imports),
            }
            examples["huey"] = [(f.file_path, f.line) for f in huey_imports[:5]]

        # APScheduler
        apscheduler_imports = index.find_imports_matching("apscheduler", limit=20)
        if apscheduler_imports:
            libraries["apscheduler"] = {
                "name": "APScheduler",
                "import_count": len(apscheduler_imports),
            }
            examples["apscheduler"] = [(f.file_path, f.line) for f in apscheduler_imports[:5]]

        # arq (async)
        arq_imports = index.find_imports_matching("arq", limit=20)
        arq_imports = [i for i in arq_imports if i.module in ("arq", "arq.jobs", "arq.worker")]
        if arq_imports:
            libraries["arq"] = {
                "name": "arq",
                "import_count": len(arq_imports),
            }
            examples["arq"] = [(f.file_path, f.line) for f in arq_imports[:5]]

        if not libraries:
            return result

        library_names = [lib["name"] for lib in libraries.values()]
        primary = max(libraries, key=lambda k: libraries[k]["import_count"])

        title = f"Background tasks: {libraries[primary]['name']}"
        description = f"Uses {libraries[primary]['name']} for background task processing."
        if len(libraries) > 1:
            others = [name for name in library_names if name != libraries[primary]["name"]]
            description += f" Also uses: {', '.join(others)}."

        confidence = min(0.9, 0.7 + libraries[primary]["import_count"] * 0.02)

        evidence = []
        for file_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, file_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.background_tasks",
            category="async",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "libraries": list(libraries.keys()),
                "primary_library": primary,
                "library_details": libraries,
            },
        ))

        return result
