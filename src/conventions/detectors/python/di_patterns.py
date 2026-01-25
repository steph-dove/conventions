"""Python dependency injection conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonDIConventionsDetector(PythonDetector):
    """Detect Python dependency injection patterns."""

    name = "python_di_conventions"
    description = "Detects dependency injection patterns (Depends, containers, singletons)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect dependency injection patterns including Depends, containers, and singletons."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect DI patterns
        self._detect_di_style(ctx, index, result)

        return result

    def _detect_di_style(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect the dominant DI style."""
        patterns: Counter[str] = Counter()
        pattern_examples: dict[str, list[tuple[str, int, str]]] = {}

        # Check for FastAPI Depends pattern
        depends_count = 0
        depends_names: Counter[str] = Counter()

        # First, check if FastAPI/Starlette is actually used
        has_fastapi = False
        for rel_path, imp in index.get_all_imports():
            if imp.module in ("fastapi", "starlette") or imp.module.startswith("fastapi.") or imp.module.startswith("starlette."):
                has_fastapi = True
                break

        for rel_path, call in index.get_all_calls():
            # Skip test and docs files
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            if call.name == "Depends":
                depends_count += 1
                patterns["fastapi_depends"] += 1

                if "fastapi_depends" not in pattern_examples:
                    pattern_examples["fastapi_depends"] = []
                if len(pattern_examples["fastapi_depends"]) < 5:
                    pattern_examples["fastapi_depends"].append((rel_path, call.line, "Depends"))

        # Only count common dependency function names if FastAPI is used or Depends() was found
        if has_fastapi or depends_count > 0:
            for rel_path, func in index.get_all_functions():
                # Skip test and docs files
                file_idx = index.files.get(rel_path)
                if file_idx and file_idx.role in ("test", "docs"):
                    continue

                if func.name in ("get_db", "get_session", "get_current_user", "get_settings"):
                    depends_names[func.name] += 1
                    patterns["fastapi_depends"] += 1

                    if "fastapi_depends" not in pattern_examples:
                        pattern_examples["fastapi_depends"] = []
                    if len(pattern_examples["fastapi_depends"]) < 5:
                        pattern_examples["fastapi_depends"].append((rel_path, func.line, func.name))

        # Check for DI container libraries
        # Use exact module matching to avoid false positives (e.g., "threading" contains "di")
        container_libs = {
            "dependency_injector",
            "injector",
            "punq",
            "lagom",
            "pinject",
            "python_inject",
            "kink",
        }

        for rel_path, imp in index.get_all_imports():
            # Check if the import module starts with or equals a known DI library
            module_parts = imp.module.split(".")
            root_module = module_parts[0]
            if root_module in container_libs:
                patterns["container_di"] += 1
                if "container_di" not in pattern_examples:
                    pattern_examples["container_di"] = []
                pattern_examples["container_di"].append((rel_path, imp.line, root_module))

        # Check for Container classes only if we already found DI library imports
        # (to avoid false positives from unrelated Container classes)
        if patterns.get("container_di", 0) > 0:
            for rel_path, cls in index.get_all_classes():
                if cls.name.endswith("Container") and "DI" in cls.name.upper():
                    patterns["container_di"] += 1
                    if "container_di" not in pattern_examples:
                        pattern_examples["container_di"] = []
                    pattern_examples["container_di"].append((rel_path, cls.line, cls.name))

        # NOTE: Module-level singleton detection removed due to high false positive rate.
        # The heuristic of checking for "Client/Connection/Session" calls in early lines
        # was incorrectly flagging standard library usage (e.g., threading imports) as DI patterns.

        if not patterns:
            return

        # Determine dominant pattern
        total = sum(patterns.values())
        dominant_pattern, dominant_count = patterns.most_common(1)[0]
        dominant_ratio = dominant_count / total if total else 0

        # Map to friendly names and descriptions
        pattern_info = {
            "fastapi_depends": {
                "name": "FastAPI Depends",
                "title": "FastAPI dependency injection pattern",
                "desc": "Uses FastAPI's Depends() for dependency injection",
            },
            "container_di": {
                "name": "Container-based DI",
                "title": "Container-based dependency injection",
                "desc": "Uses a DI container library for dependency management",
            },
        }

        if len(patterns) == 1:
            info = pattern_info.get(dominant_pattern, {
                "name": dominant_pattern,
                "title": f"DI pattern: {dominant_pattern}",
                "desc": f"Uses {dominant_pattern} pattern",
            })
            title = info["title"]
            description = f"{info['desc']}. Found {dominant_count} usages."
            confidence = min(0.9, 0.6 + dominant_count * 0.02)
        else:
            # Multiple patterns
            pattern_names = [pattern_info.get(p, {"name": p})["name"] for p in patterns.keys()]
            title = f"Mixed DI patterns: {pattern_info.get(dominant_pattern, {'name': dominant_pattern})['name']} dominant"
            description = (
                f"Uses multiple DI patterns. "
                f"Primary: {pattern_info.get(dominant_pattern, {'name': dominant_pattern})['name']} ({dominant_count}/{total}). "
                f"Also uses: {', '.join(p for p in pattern_names if p != pattern_info.get(dominant_pattern, {'name': dominant_pattern})['name'])}."
            )
            confidence = min(0.75, 0.5 + dominant_ratio * 0.25)

        # Build evidence
        evidence = []
        for rel_path, line, name in pattern_examples.get(dominant_pattern, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.di_style",
            category="dependency_injection",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "pattern_counts": dict(patterns),
                "dominant_pattern": dominant_pattern,
                "depends_count": depends_count,
                "common_dependency_names": dict(depends_names.most_common(10)),
            },
        ))
