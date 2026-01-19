"""Go logging conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult
from .base import GoDetector
from .index import GoIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class GoLoggingDetector(GoDetector):
    """Detect Go logging conventions."""

    name = "go_logging"
    description = "Detects Go logging library and patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go logging conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect logging library
        self._detect_logging_library(ctx, index, result)

        # Detect structured vs printf logging
        self._detect_logging_style(ctx, index, result)

        return result

    def _detect_logging_library(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect logging library usage."""
        libraries = {
            "zap": "go.uber.org/zap",
            "zerolog": "github.com/rs/zerolog",
            "logrus": "github.com/sirupsen/logrus",
            "slog": "log/slog",
            "log": "log",
        }

        library_counts: Counter[str] = Counter()
        examples: dict[str, list[tuple[str, int]]] = {}

        for name, pkg in libraries.items():
            imports = index.find_imports_matching(pkg, limit=30)
            if imports:
                library_counts[name] = len(imports)
                examples[name] = [(r, l) for r, _, l in imports[:5]]

        if not library_counts:
            return

        primary, primary_count = library_counts.most_common(1)[0]

        library_names = {
            "zap": "Uber Zap",
            "zerolog": "Zerolog",
            "logrus": "Logrus",
            "slog": "slog (stdlib)",
            "log": "Standard log",
        }

        if len(library_counts) == 1:
            title = f"Logging with {library_names.get(primary, primary)}"
            description = (
                f"Uses {library_names.get(primary, primary)} for logging. "
                f"Found in {primary_count} files."
            )
        else:
            others = [library_names.get(n, n) for n in library_counts if n != primary]
            title = f"Primary logging: {library_names.get(primary, primary)}"
            description = (
                f"Primarily uses {library_names.get(primary, primary)}. "
                f"Also found: {', '.join(others)}."
            )

        confidence = min(0.95, 0.7 + primary_count * 0.02)

        evidence = []
        for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.logging_library",
            category="observability",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "library_counts": dict(library_counts),
                "primary_library": primary,
            },
        ))

    def _detect_logging_style(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect structured vs printf-style logging."""
        # Structured logging patterns (zap, zerolog, logrus, slog)
        structured_patterns = [
            r"\.Info\([^)]*\)\.(?:Str|Int|Bool|Err|Float)",  # zerolog
            r"\.With\(.*\)\.Info",  # zap, logrus
            r"logger\.Info\([\"'][^)]*[\"'],\s*(?:zap|slog)\.",  # zap, slog
            r"slog\.Info\([^,]+,",  # slog with attrs
        ]

        # Printf-style patterns
        printf_patterns = [
            r"log\.Printf\(",
            r"log\.Println\(",
            r"fmt\.Printf\(",
            r"logger\.Infof\(",
            r"logger\.Printf\(",
        ]

        structured_count = 0
        printf_count = 0

        for pattern in structured_patterns:
            structured_count += index.count_pattern(pattern, exclude_tests=True)

        for pattern in printf_patterns:
            printf_count += index.count_pattern(pattern, exclude_tests=True)

        total = structured_count + printf_count
        if total < 5:
            return

        structured_ratio = structured_count / total if total else 0

        if structured_ratio >= 0.7:
            title = "Structured logging"
            description = (
                f"Uses structured logging with key-value pairs. "
                f"Structured: {structured_count}, Printf-style: {printf_count}."
            )
            confidence = min(0.9, 0.6 + structured_ratio * 0.3)
        elif structured_ratio >= 0.3:
            title = "Mixed logging styles"
            description = (
                f"Uses both structured and printf-style logging. "
                f"Structured: {structured_count}, Printf-style: {printf_count}."
            )
            confidence = 0.7
        else:
            title = "Printf-style logging"
            description = (
                f"Uses printf-style logging. "
                f"Printf-style: {printf_count}, Structured: {structured_count}."
            )
            confidence = min(0.85, 0.6 + (1 - structured_ratio) * 0.25)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.structured_logging",
            category="observability",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=[],
            stats={
                "structured_count": structured_count,
                "printf_count": printf_count,
                "structured_ratio": round(structured_ratio, 3),
            },
        ))
