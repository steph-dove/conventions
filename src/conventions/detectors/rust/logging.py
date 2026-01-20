"""Rust logging conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import RustDetector
from .index import make_evidence


@DetectorRegistry.register
class RustLoggingDetector(RustDetector):
    """Detect Rust logging conventions."""

    name = "rust_logging"
    description = "Detects logging and tracing frameworks"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect logging conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        frameworks: dict[str, dict] = {}
        examples: list[tuple[str, int]] = []

        # Check for tracing
        tracing_uses = index.find_uses_matching("tracing", limit=50)
        if tracing_uses:
            frameworks["tracing"] = {
                "name": "tracing",
                "type": "structured",
                "count": len(tracing_uses),
            }
            examples.extend([(r, ln) for r, _, ln in tracing_uses[:3]])

            # Check for tracing-subscriber
            subscriber_uses = index.find_uses_matching("tracing_subscriber", limit=20)
            if subscriber_uses:
                frameworks["tracing"]["subscriber"] = True

            # Check for instrument attribute
            instrument_attrs = index.search_pattern(
                r"#\[(?:tracing::)?instrument",
                limit=30,
                exclude_tests=True,
            )
            if instrument_attrs:
                frameworks["tracing"]["instrument_count"] = len(instrument_attrs)

        # Check for log crate
        log_uses = index.find_uses_matching("log", limit=50)
        # Filter to exact "log" crate
        log_uses = [u for u in log_uses if u[1] == "log" or u[1].startswith("log::")]
        if log_uses:
            frameworks["log"] = {
                "name": "log",
                "type": "facade",
                "count": len(log_uses),
            }
            if not examples:
                examples.extend([(r, ln) for r, _, ln in log_uses[:3]])

        # Check for env_logger
        env_logger_uses = index.find_uses_matching("env_logger", limit=20)
        if env_logger_uses:
            frameworks["env_logger"] = {
                "name": "env_logger",
                "type": "backend",
                "count": len(env_logger_uses),
            }

        # Check for pretty_env_logger
        pretty_env_uses = index.find_uses_matching("pretty_env_logger", limit=10)
        if pretty_env_uses:
            frameworks["pretty_env_logger"] = {
                "name": "pretty_env_logger",
                "type": "backend",
                "count": len(pretty_env_uses),
            }

        # Check for fern
        fern_uses = index.find_uses_matching("fern", limit=20)
        if fern_uses:
            frameworks["fern"] = {
                "name": "fern",
                "type": "backend",
                "count": len(fern_uses),
            }

        # Check for slog
        slog_uses = index.find_uses_matching("slog", limit=30)
        if slog_uses:
            frameworks["slog"] = {
                "name": "slog",
                "type": "structured",
                "count": len(slog_uses),
            }

        # Check for flexi_logger
        flexi_uses = index.find_uses_matching("flexi_logger", limit=20)
        if flexi_uses:
            frameworks["flexi_logger"] = {
                "name": "flexi_logger",
                "type": "backend",
                "count": len(flexi_uses),
            }

        # Count log macro usages
        log_macro_patterns = [
            (r"trace!\(", "trace"),
            (r"debug!\(", "debug"),
            (r"info!\(", "info"),
            (r"warn!\(", "warn"),
            (r"error!\(", "error"),
        ]

        log_levels: dict[str, int] = {}
        for pattern, level in log_macro_patterns:
            count = index.count_pattern(pattern, exclude_tests=True)
            if count > 0:
                log_levels[level] = count

        if not frameworks and not log_levels:
            return result

        # Determine primary
        if "tracing" in frameworks:
            primary = "tracing"
            style = "structured async tracing"
        elif "slog" in frameworks:
            primary = "slog"
            style = "structured logging"
        elif "log" in frameworks:
            primary = "log"
            style = "log facade"
            # Find backend
            backends = [k for k in ["env_logger", "pretty_env_logger", "fern", "flexi_logger"] if k in frameworks]
            if backends:
                style += f" with {frameworks[backends[0]]['name']}"
        else:
            primary = list(frameworks.keys())[0] if frameworks else "unknown"
            style = "logging"

        fw_info = frameworks.get(primary, {"name": primary})
        title = f"Logging: {fw_info.get('name', primary)}"
        description = f"Uses {fw_info.get('name', primary)} for {style}."

        if "tracing" in frameworks and frameworks["tracing"].get("instrument_count", 0) > 0:
            description += f" {frameworks['tracing']['instrument_count']} instrumented functions."

        total_logs = sum(log_levels.values())
        if total_logs > 0:
            description += f" {total_logs} log statement(s)."

        confidence = 0.9

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.logging",
            category="observability",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "frameworks": list(frameworks.keys()),
                "primary_framework": primary,
                "log_levels": log_levels,
                "total_log_statements": total_logs,
                "framework_details": frameworks,
            },
        ))

        return result
