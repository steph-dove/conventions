"""Python feature flags detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonFeatureFlagsDetector(PythonDetector):
    """Detect Python feature flag patterns."""

    name = "python_feature_flags"
    description = "Detects feature flag libraries and patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect feature flag patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_feature_flags(ctx, index, result)

        return result

    def _detect_feature_flags(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect feature flag library usage."""
        flag_libs: Counter[str] = Counter()
        flag_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # Skip test files
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # LaunchDarkly
            if "ldclient" in imp.module or "launchdarkly" in imp.module:
                flag_libs["launchdarkly"] += 1
                if "launchdarkly" not in flag_examples:
                    flag_examples["launchdarkly"] = []
                flag_examples["launchdarkly"].append((rel_path, imp.line))

            # Flagsmith
            if "flagsmith" in imp.module:
                flag_libs["flagsmith"] += 1
                if "flagsmith" not in flag_examples:
                    flag_examples["flagsmith"] = []
                flag_examples["flagsmith"].append((rel_path, imp.line))

            # Unleash
            if "UnleashClient" in imp.names or "unleash" in imp.module:
                flag_libs["unleash"] += 1
                if "unleash" not in flag_examples:
                    flag_examples["unleash"] = []
                flag_examples["unleash"].append((rel_path, imp.line))

            # Split.io
            if "splitio" in imp.module:
                flag_libs["split"] += 1
                if "split" not in flag_examples:
                    flag_examples["split"] = []
                flag_examples["split"].append((rel_path, imp.line))

            # flipper-client
            if "flipper" in imp.module:
                flag_libs["flipper"] += 1
                if "flipper" not in flag_examples:
                    flag_examples["flipper"] = []
                flag_examples["flipper"].append((rel_path, imp.line))

            # growthbook
            if "growthbook" in imp.module:
                flag_libs["growthbook"] += 1
                if "growthbook" not in flag_examples:
                    flag_examples["growthbook"] = []
                flag_examples["growthbook"].append((rel_path, imp.line))

            # feature-flags (simple library)
            if "feature_flags" in imp.module:
                flag_libs["feature_flags"] += 1
                if "feature_flags" not in flag_examples:
                    flag_examples["feature_flags"] = []
                flag_examples["feature_flags"].append((rel_path, imp.line))

        # Check for feature flag usage patterns
        feature_flag_calls = 0
        for rel_path, call in index.get_all_calls():
            # Common feature flag method names
            if any(x in call.name.lower() for x in [
                "is_enabled", "is_feature_enabled", "variation",
                "get_flag", "flag_enabled", "feature_enabled",
                "is_on", "is_active"
            ]):
                feature_flag_calls += 1

        # Check for environment-based feature flags
        env_flags = 0
        for rel_path, file_idx in index.files.items():
            if file_idx.role in ("test", "docs"):
                continue

            for line in file_idx.lines:
                line_lower = line.lower()
                if "feature_" in line_lower and ("enabled" in line_lower or "flag" in line_lower):
                    env_flags += 1
                elif "ff_" in line_lower or "_ff" in line_lower:
                    env_flags += 1

        if env_flags > 5:
            flag_libs["env_flags"] = env_flags

        if not flag_libs:
            return

        primary, primary_count = flag_libs.most_common(1)[0]

        lib_names = {
            "launchdarkly": "LaunchDarkly",
            "flagsmith": "Flagsmith",
            "unleash": "Unleash",
            "split": "Split.io",
            "flipper": "Flipper",
            "growthbook": "GrowthBook",
            "feature_flags": "feature-flags",
            "env_flags": "environment variables",
        }

        # Quality assessment
        managed_services = ["launchdarkly", "split", "flagsmith"]
        self_hosted = ["unleash", "growthbook", "flipper"]

        if primary in managed_services:
            quality = "managed"
            title = f"Feature flags: {lib_names.get(primary, primary)} (managed)"
        elif primary in self_hosted:
            quality = "self_hosted"
            title = f"Feature flags: {lib_names.get(primary, primary)} (self-hosted)"
        elif primary == "env_flags":
            quality = "basic"
            title = "Feature flags: environment variables"
        else:
            quality = "library"
            title = f"Feature flags: {lib_names.get(primary, primary)}"

        description = f"Uses {lib_names.get(primary, primary)} for feature flags."
        if feature_flag_calls > 0:
            description += f" Found {feature_flag_calls} flag check(s)."

        confidence = min(0.85, 0.6 + primary_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in flag_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.feature_flags",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "flag_library_counts": dict(flag_libs),
                "primary_library": primary,
                "feature_flag_calls": feature_flag_calls,
                "quality": quality,
            },
        ))
