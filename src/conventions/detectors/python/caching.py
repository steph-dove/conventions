"""Python caching patterns detector."""

from __future__ import annotations

import re

from ..base import DetectorContext, DetectorResult, PythonDetector
from .index import PythonIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class PythonCachingDetector(PythonDetector):
    """Detect Python caching patterns."""

    name = "python_caching"
    description = "Detects Python caching patterns (lru_cache, redis, cachetools)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Python caching patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        caching_methods: dict[str, dict] = {}
        examples: dict[str, list[tuple[str, int]]] = {}

        # functools.lru_cache / cache
        lru_cache_count = 0
        cache_count = 0
        for file_idx in index.files.values():
            for func in file_idx.functions:
                for decorator in func.decorators:
                    if "lru_cache" in decorator:
                        lru_cache_count += 1
                        if "lru_cache" not in examples:
                            examples["lru_cache"] = []
                        if len(examples["lru_cache"]) < 10:
                            examples["lru_cache"].append((file_idx.relative_path, func.line))
                    elif decorator == "cache" or "functools.cache" in decorator:
                        cache_count += 1
                        if "cache" not in examples:
                            examples["cache"] = []
                        if len(examples["cache"]) < 10:
                            examples["cache"].append((file_idx.relative_path, func.line))

        if lru_cache_count > 0:
            caching_methods["lru_cache"] = {
                "name": "functools.lru_cache",
                "count": lru_cache_count,
            }
        if cache_count > 0:
            caching_methods["cache"] = {
                "name": "functools.cache",
                "count": cache_count,
            }

        # Redis
        redis_imports = index.find_imports_matching("redis", limit=20)
        if redis_imports:
            caching_methods["redis"] = {
                "name": "Redis",
                "import_count": len(redis_imports),
            }
            examples["redis"] = [(f.file_path, f.line) for f in redis_imports[:5]]

        # cachetools
        cachetools_imports = index.find_imports_matching("cachetools", limit=20)
        if cachetools_imports:
            caching_methods["cachetools"] = {
                "name": "cachetools",
                "import_count": len(cachetools_imports),
            }
            examples["cachetools"] = [(f.file_path, f.line) for f in cachetools_imports[:5]]

        # aiocache
        aiocache_imports = index.find_imports_matching("aiocache", limit=20)
        if aiocache_imports:
            caching_methods["aiocache"] = {
                "name": "aiocache",
                "import_count": len(aiocache_imports),
            }
            examples["aiocache"] = [(f.file_path, f.line) for f in aiocache_imports[:5]]

        # diskcache
        diskcache_imports = index.find_imports_matching("diskcache", limit=20)
        if diskcache_imports:
            caching_methods["diskcache"] = {
                "name": "diskcache",
                "import_count": len(diskcache_imports),
            }
            examples["diskcache"] = [(f.file_path, f.line) for f in diskcache_imports[:5]]

        if not caching_methods:
            return result

        method_names = [m["name"] for m in caching_methods.values()]

        # Determine primary caching method
        def get_count(key):
            m = caching_methods[key]
            return m.get("count", 0) + m.get("import_count", 0)

        primary = max(caching_methods, key=get_count)

        title = f"Caching: {', '.join(method_names)}"
        description = f"Uses {', '.join(method_names)} for caching."

        # Redis or aiocache are more sophisticated
        if "redis" in caching_methods or "aiocache" in caching_methods:
            confidence = 0.9
        else:
            confidence = 0.8

        evidence = []
        for file_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, file_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.caching",
            category="performance",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "caching_methods": list(caching_methods.keys()),
                "primary_method": primary,
                "method_details": caching_methods,
            },
        ))

        return result
