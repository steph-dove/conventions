"""Rust unsafe code conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from .base import RustDetector
from .index import make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class RustUnsafeDetector(RustDetector):
    """Detect Rust unsafe code conventions."""

    name = "rust_unsafe"
    description = "Analyzes unsafe code usage and safety patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect unsafe code conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Count unsafe blocks
        unsafe_blocks = index.search_pattern(
            r"\bunsafe\s*\{",
            limit=100,
            exclude_tests=True,
        )

        # Count unsafe functions
        unsafe_fns = index.search_pattern(
            r"\bunsafe\s+fn\s+\w+",
            limit=100,
            exclude_tests=True,
        )

        # Count unsafe impl
        unsafe_impls = index.search_pattern(
            r"\bunsafe\s+impl\b",
            limit=50,
            exclude_tests=True,
        )

        # Count raw pointer operations
        raw_ptr_ops = index.count_pattern(
            r"\*(?:const|mut)\s+\w+",
            exclude_tests=True,
        )

        # Check for FFI
        extern_blocks = index.search_pattern(
            r'extern\s+"C"\s*\{',
            limit=30,
            exclude_tests=True,
        )

        # Check for #[no_mangle]
        no_mangle = index.search_pattern(
            r"#\[no_mangle\]",
            limit=30,
            exclude_tests=True,
        )

        # Check for #![forbid(unsafe_code)]
        forbid_unsafe = index.search_pattern(
            r"#!\[forbid\([^)]*unsafe_code",
            limit=10,
        )

        # Check for #![deny(unsafe_code)]
        deny_unsafe = index.search_pattern(
            r"#!\[deny\([^)]*unsafe_code",
            limit=10,
        )

        total_unsafe = len(unsafe_blocks) + len(unsafe_fns)

        if total_unsafe == 0 and len(extern_blocks) == 0:
            # Check if unsafe is explicitly forbidden
            if forbid_unsafe or deny_unsafe:
                title = "Unsafe: Forbidden"
                description = "This crate forbids unsafe code."
                confidence = 0.95

                result.rules.append(self.make_rule(
                    rule_id="rust.conventions.unsafe_code",
                    category="safety",
                    title=title,
                    description=description,
                    confidence=confidence,
                    language="rust",
                    evidence=[],
                    stats={
                        "unsafe_forbidden": True,
                        "unsafe_block_count": 0,
                        "unsafe_fn_count": 0,
                    },
                ))
            return result

        examples: list[tuple[str, int]] = []
        examples.extend([(r, l) for r, l, _ in unsafe_blocks[:3]])
        examples.extend([(r, l) for r, l, _ in unsafe_fns[:2]])

        # Determine unsafe category
        has_ffi = len(extern_blocks) > 0 or len(no_mangle) > 0

        if has_ffi:
            category = "FFI"
            description = f"Uses unsafe for FFI. {len(extern_blocks)} extern block(s)."
        elif total_unsafe < 5:
            category = "minimal"
            description = f"Minimal unsafe usage. {total_unsafe} unsafe block(s)."
        elif total_unsafe < 20:
            category = "moderate"
            description = f"Moderate unsafe usage. {total_unsafe} unsafe block(s)."
        else:
            category = "extensive"
            description = f"Extensive unsafe usage. {total_unsafe} unsafe block(s)."

        title = f"Unsafe: {category}"

        if len(unsafe_impls) > 0:
            description += f" {len(unsafe_impls)} unsafe impl(s)."

        # Check for SAFETY comments
        safety_comments = index.search_pattern(
            r"//\s*SAFETY:",
            limit=50,
            exclude_tests=True,
        )
        if safety_comments:
            description += f" Has {len(safety_comments)} SAFETY comment(s)."

        confidence = 0.9

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.unsafe_code",
            category="safety",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "unsafe_block_count": len(unsafe_blocks),
                "unsafe_fn_count": len(unsafe_fns),
                "unsafe_impl_count": len(unsafe_impls),
                "extern_block_count": len(extern_blocks),
                "raw_ptr_ops": raw_ptr_ops,
                "safety_comment_count": len(safety_comments),
                "has_ffi": has_ffi,
                "category": category,
            },
        ))

        return result
