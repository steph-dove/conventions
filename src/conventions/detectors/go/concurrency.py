"""Go concurrency conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import GoDetector
from .index import GoIndex, make_evidence


@DetectorRegistry.register
class GoConcurrencyDetector(GoDetector):
    """Detect Go concurrency conventions."""

    name = "go_concurrency"
    description = "Detects Go concurrency patterns and practices"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go concurrency conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect goroutine patterns
        self._detect_goroutine_patterns(ctx, index, result)

        # Detect channel usage
        self._detect_channel_usage(ctx, index, result)

        # Detect context.Context usage
        self._detect_context_usage(ctx, index, result)

        # Detect sync primitives
        self._detect_sync_primitives(ctx, index, result)

        return result

    def _detect_goroutine_patterns(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect goroutine usage patterns."""
        # go keyword followed by function call
        go_pattern = r'\bgo\s+\w+'
        matches = index.search_pattern(go_pattern, limit=100, exclude_tests=True)

        if len(matches) < 3:
            return

        # Check for errgroup usage
        errgroup_imports = index.find_imports_matching("golang.org/x/sync/errgroup")
        uses_errgroup = len(errgroup_imports) > 0

        title = "Uses goroutines"
        if uses_errgroup:
            title = "Goroutines with errgroup"
            description = (
                f"Uses goroutines with errgroup for error handling. "
                f"Found {len(matches)} goroutine invocations."
            )
        else:
            description = (
                f"Uses goroutines for concurrency. "
                f"Found {len(matches)} goroutine invocations."
            )

        confidence = min(0.9, 0.6 + len(matches) * 0.02)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.goroutine_patterns",
            category="concurrency",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "goroutine_count": len(matches),
                "uses_errgroup": uses_errgroup,
            },
        ))

    def _detect_channel_usage(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect channel usage patterns."""
        # Channel declarations: make(chan ...)
        make_chan_pattern = r'make\s*\(\s*chan\s+'
        make_chan_count = index.count_pattern(make_chan_pattern, exclude_tests=True)

        # Channel operations: <- chan, chan <-
        send_recv_pattern = r'<-\s*\w+|\w+\s*<-'
        send_recv_count = index.count_pattern(send_recv_pattern, exclude_tests=True)

        # Select statements
        select_pattern = r'\bselect\s*\{'
        select_count = index.count_pattern(select_pattern, exclude_tests=True)

        total = make_chan_count + select_count
        if total < 2:
            return

        matches = index.search_pattern(make_chan_pattern, limit=20)

        title = "Channel-based concurrency"
        description = (
            f"Uses Go channels for coordination. "
            f"Channel creations: {make_chan_count}, Select: {select_count}."
        )
        confidence = min(0.9, 0.6 + total * 0.04)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.channel_usage",
            category="concurrency",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "channel_creation_count": make_chan_count,
                "select_count": select_count,
                "send_recv_count": send_recv_count,
            },
        ))

    def _detect_context_usage(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect context.Context usage patterns."""
        # Context imports
        ctx_imports = index.find_imports_matching("context", limit=100)
        if len(ctx_imports) < 3:
            return

        # Functions with context as first param
        ctx_param_pattern = r'func\s+(?:\([^)]+\)\s+)?\w+\s*\(\s*ctx\s+context\.Context'
        ctx_param_count = index.count_pattern(ctx_param_pattern, exclude_tests=True)

        # context.Background() and context.TODO()
        background_pattern = r'context\.(?:Background|TODO)\(\)'
        background_count = index.count_pattern(background_pattern, exclude_tests=True)

        # context.WithCancel/Timeout/Deadline
        with_pattern = r'context\.With(?:Cancel|Timeout|Deadline|Value)\('
        with_count = index.count_pattern(with_pattern, exclude_tests=True)

        total_usage = ctx_param_count + with_count
        if total_usage < 3:
            return

        matches = index.search_pattern(ctx_param_pattern, limit=20)

        title = "Context propagation"
        description = (
            f"Propagates context.Context through call chains. "
            f"Functions with ctx param: {ctx_param_count}, Context wrappers: {with_count}."
        )
        confidence = min(0.95, 0.7 + ctx_param_count * 0.02)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.context_usage",
            category="concurrency",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "ctx_param_count": ctx_param_count,
                "background_todo_count": background_count,
                "with_wrapper_count": with_count,
            },
        ))

    def _detect_sync_primitives(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect sync package primitive usage."""
        # sync.Mutex, sync.RWMutex
        mutex_pattern = r'sync\.(?:RW)?Mutex'
        mutex_count = index.count_pattern(mutex_pattern, exclude_tests=True)

        # sync.WaitGroup
        wg_pattern = r'sync\.WaitGroup'
        wg_count = index.count_pattern(wg_pattern, exclude_tests=True)

        # sync.Once
        once_pattern = r'sync\.Once'
        once_count = index.count_pattern(once_pattern, exclude_tests=True)

        # sync.Map
        map_pattern = r'sync\.Map'
        map_count = index.count_pattern(map_pattern, exclude_tests=True)

        total = mutex_count + wg_count + once_count + map_count
        if total < 3:
            return

        matches = index.search_pattern(r'sync\.(?:RW)?Mutex|sync\.WaitGroup', limit=20)

        parts = []
        if mutex_count:
            parts.append(f"Mutex: {mutex_count}")
        if wg_count:
            parts.append(f"WaitGroup: {wg_count}")
        if once_count:
            parts.append(f"Once: {once_count}")
        if map_count:
            parts.append(f"Map: {map_count}")

        title = "Sync primitives"
        description = f"Uses sync package primitives. {', '.join(parts)}."
        confidence = min(0.9, 0.6 + total * 0.03)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.sync_primitives",
            category="concurrency",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "mutex_count": mutex_count,
                "waitgroup_count": wg_count,
                "once_count": once_count,
                "map_count": map_count,
            },
        ))
