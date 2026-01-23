"""Python observability conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonObservabilityConventionsDetector(PythonDetector):
    """Detect Python observability conventions (tracing, metrics, correlation IDs)."""

    name = "python_observability_conventions"
    description = "Detects tracing, metrics, and correlation ID patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect tracing, metrics, and correlation ID patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect tracing
        self._detect_tracing(ctx, index, result)

        # Detect metrics
        self._detect_metrics(ctx, index, result)

        # Detect correlation IDs
        self._detect_correlation_ids(ctx, index, result)

        return result

    def _detect_tracing(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect tracing library usage."""
        tracing_libs: Counter[str] = Counter()
        tracing_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # OpenTelemetry
            if "opentelemetry" in imp.module:
                tracing_libs["opentelemetry"] += 1
                if "opentelemetry" not in tracing_examples:
                    tracing_examples["opentelemetry"] = []
                tracing_examples["opentelemetry"].append((rel_path, imp.line))

            # OpenTracing (legacy)
            if "opentracing" in imp.module:
                tracing_libs["opentracing"] += 1
                if "opentracing" not in tracing_examples:
                    tracing_examples["opentracing"] = []
                tracing_examples["opentracing"].append((rel_path, imp.line))

            # Jaeger client
            if "jaeger_client" in imp.module:
                tracing_libs["jaeger"] += 1
                if "jaeger" not in tracing_examples:
                    tracing_examples["jaeger"] = []
                tracing_examples["jaeger"].append((rel_path, imp.line))

            # Sentry tracing
            if "sentry_sdk" in imp.module:
                tracing_libs["sentry"] += 1
                if "sentry" not in tracing_examples:
                    tracing_examples["sentry"] = []
                tracing_examples["sentry"].append((rel_path, imp.line))

            # ddtrace (Datadog)
            if "ddtrace" in imp.module:
                tracing_libs["datadog"] += 1
                if "datadog" not in tracing_examples:
                    tracing_examples["datadog"] = []
                tracing_examples["datadog"].append((rel_path, imp.line))

        # Check for span creation patterns
        for rel_path, call in index.get_all_calls():
            if any(x in call.name for x in ["start_span", "start_as_current_span", "tracer.start"]):
                if "opentelemetry" in tracing_libs or "opentracing" in tracing_libs:
                    tracing_libs["spans_created"] = tracing_libs.get("spans_created", 0) + 1
                    if "spans" not in tracing_examples:
                        tracing_examples["spans"] = []
                    if len(tracing_examples["spans"]) < 5:
                        tracing_examples["spans"].append((rel_path, call.line))

        if not tracing_libs:
            return

        # Determine pattern
        # Filter out span count for library detection
        lib_counts = {k: v for k, v in tracing_libs.items() if k != "spans_created"}
        if not lib_counts:
            return

        primary, primary_count = Counter(lib_counts).most_common(1)[0]
        span_count = tracing_libs.get("spans_created", 0)

        lib_names = {
            "opentelemetry": "OpenTelemetry",
            "opentracing": "OpenTracing",
            "jaeger": "Jaeger",
            "sentry": "Sentry",
            "datadog": "Datadog (ddtrace)",
        }

        if span_count > 0:
            title = f"Distributed tracing with {lib_names.get(primary, primary)}"
            description = (
                f"Uses {lib_names.get(primary, primary)} for distributed tracing. "
                f"Found {span_count} span creation patterns."
            )
            confidence = min(0.9, 0.6 + span_count * 0.03)
        else:
            title = f"Tracing library: {lib_names.get(primary, primary)}"
            description = (
                f"Imports {lib_names.get(primary, primary)} tracing library. "
                f"Found {primary_count} imports."
            )
            confidence = min(0.75, 0.5 + primary_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in tracing_examples.get(primary, [])[:3]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)
        for rel_path, line in tracing_examples.get("spans", [])[:2]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.tracing",
            category="observability",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence[:ctx.max_evidence_snippets],
            stats={
                "tracing_library_counts": dict(lib_counts),
                "primary_library": primary,
                "spans_created": span_count,
            },
        ))

    def _detect_metrics(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect metrics library usage."""
        metrics_libs: Counter[str] = Counter()
        metrics_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # prometheus_client
            if "prometheus_client" in imp.module or "prometheus" in imp.module:
                metrics_libs["prometheus"] += 1
                if "prometheus" not in metrics_examples:
                    metrics_examples["prometheus"] = []
                metrics_examples["prometheus"].append((rel_path, imp.line))

            # statsd
            if "statsd" in imp.module or "datadog" in imp.module:
                metrics_libs["statsd"] += 1
                if "statsd" not in metrics_examples:
                    metrics_examples["statsd"] = []
                metrics_examples["statsd"].append((rel_path, imp.line))

            # OpenTelemetry metrics
            if "opentelemetry" in imp.module and "metrics" in imp.module:
                metrics_libs["opentelemetry_metrics"] += 1
                if "opentelemetry_metrics" not in metrics_examples:
                    metrics_examples["opentelemetry_metrics"] = []
                metrics_examples["opentelemetry_metrics"].append((rel_path, imp.line))

            # aioprometheus
            if "aioprometheus" in imp.module:
                metrics_libs["aioprometheus"] += 1
                if "aioprometheus" not in metrics_examples:
                    metrics_examples["aioprometheus"] = []
                metrics_examples["aioprometheus"].append((rel_path, imp.line))

        # Check for metric creation patterns
        for rel_path, call in index.get_all_calls():
            if any(x in call.name for x in ["Counter", "Gauge", "Histogram", "Summary"]):
                metrics_libs["metric_definitions"] = metrics_libs.get("metric_definitions", 0) + 1

        if not metrics_libs:
            return

        # Filter out definition count
        lib_counts = {k: v for k, v in metrics_libs.items() if k != "metric_definitions"}
        if not lib_counts:
            return

        primary, primary_count = Counter(lib_counts).most_common(1)[0]
        metric_defs = metrics_libs.get("metric_definitions", 0)

        lib_names = {
            "prometheus": "Prometheus",
            "statsd": "StatsD/Datadog",
            "opentelemetry_metrics": "OpenTelemetry Metrics",
            "aioprometheus": "aioprometheus",
        }

        if metric_defs > 0:
            title = f"Application metrics with {lib_names.get(primary, primary)}"
            description = (
                f"Uses {lib_names.get(primary, primary)} for application metrics. "
                f"Found {metric_defs} metric definitions."
            )
            confidence = min(0.9, 0.6 + metric_defs * 0.03)
        else:
            title = f"Metrics library: {lib_names.get(primary, primary)}"
            description = (
                f"Imports {lib_names.get(primary, primary)} metrics library. "
                f"Found {primary_count} imports."
            )
            confidence = min(0.7, 0.5 + primary_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in metrics_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.metrics",
            category="observability",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "metrics_library_counts": dict(lib_counts),
                "primary_library": primary,
                "metric_definitions": metric_defs,
            },
        ))

    def _detect_correlation_ids(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect correlation/request ID patterns."""
        correlation_indicators = 0
        correlation_examples: list[tuple[str, int]] = []

        # Common correlation ID patterns
        correlation_patterns = [
            "request_id",
            "correlation_id",
            "trace_id",
            "x_request_id",
            "x-request-id",
        ]

        for rel_path, file_idx in index.files.items():
            if file_idx.role == "test":
                continue

            content = "\n".join(file_idx.lines).lower()

            for pattern in correlation_patterns:
                if pattern.replace("-", "_") in content or pattern in content:
                    # Find approximate line
                    for i, line in enumerate(file_idx.lines, 1):
                        if pattern.replace("-", "_") in line.lower() or pattern in line.lower():
                            correlation_indicators += 1
                            if len(correlation_examples) < 10:
                                correlation_examples.append((rel_path, i))
                            break
                    break  # Only count once per file per pattern

        # Check for uuid4 generation (often used for request IDs)
        uuid_count = 0
        for rel_path, call in index.get_all_calls():
            if "uuid4" in call.name or "uuid.uuid4" in call.name:
                uuid_count += 1

        if correlation_indicators < 2:
            return

        title = "Request/correlation ID propagation"
        description = (
            f"Uses request or correlation IDs for tracing. "
            f"Found {correlation_indicators} correlation ID references."
        )
        confidence = min(0.8, 0.5 + correlation_indicators * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in correlation_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.correlation_ids",
            category="observability",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "correlation_id_references": correlation_indicators,
                "uuid_generation_count": uuid_count,
            },
        ))
