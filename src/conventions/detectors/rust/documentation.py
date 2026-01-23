"""Rust documentation conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from .base import RustDetector
from .index import make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class RustDocumentationDetector(RustDetector):
    """Detect Rust documentation conventions."""

    name = "rust_documentation"
    description = "Detects documentation patterns and doc comments"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect documentation conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Count doc comments
        doc_comment_count = index.count_pattern(r"^\s*///", exclude_tests=True)
        module_doc_count = index.count_pattern(r"^\s*//!", exclude_tests=True)

        # Count documented public items
        total_pub_functions = 0
        total_pub_structs = 0
        total_pub_enums = 0
        total_pub_traits = 0

        for file_idx in index.get_non_test_files():
            total_pub_functions += sum(1 for _, _, is_pub in file_idx.functions if is_pub)
            total_pub_structs += sum(1 for _, _, is_pub in file_idx.structs if is_pub)
            total_pub_enums += sum(1 for _, _, is_pub in file_idx.enums if is_pub)
            total_pub_traits += sum(1 for _, _, is_pub in file_idx.traits if is_pub)

        total_pub_items = total_pub_functions + total_pub_structs + total_pub_enums + total_pub_traits

        # Check for doc examples (```rust blocks in docs)
        doc_examples = index.search_pattern(
            r"/// ```",
            limit=50,
            exclude_tests=True,
        )
        doc_example_count = len(doc_examples)

        # Check for #[doc = ...] attributes
        doc_attrs = index.count_pattern(r"#\[doc\s*=", exclude_tests=True)

        # Check for #![deny(missing_docs)]
        missing_docs_deny = index.search_pattern(
            r"#!\[deny\([^)]*missing_docs",
            limit=10,
        )
        enforces_docs = len(missing_docs_deny) > 0

        # Check for #![warn(missing_docs)]
        missing_docs_warn = index.search_pattern(
            r"#!\[warn\([^)]*missing_docs",
            limit=10,
        )
        warns_docs = len(missing_docs_warn) > 0

        if doc_comment_count == 0 and module_doc_count == 0:
            return result

        examples: list[tuple[str, int]] = []

        # Estimate documentation coverage
        if total_pub_items > 0:
            # Rough heuristic: assume each doc comment covers one item
            estimated_coverage = min(1.0, doc_comment_count / total_pub_items)
        else:
            estimated_coverage = 0.0

        title = f"Documentation: {doc_comment_count} doc comments"
        description = f"Has {doc_comment_count} doc comment(s)."

        if module_doc_count > 0:
            description += f" {module_doc_count} module-level doc(s)."

        if doc_example_count > 0:
            description += f" {doc_example_count} code example(s) in docs."

        if enforces_docs:
            description += " Enforces documentation (deny missing_docs)."
        elif warns_docs:
            description += " Warns on missing docs."

        # Determine quality
        quality = "minimal"
        if enforces_docs or (estimated_coverage > 0.7 and doc_example_count > 0):
            quality = "comprehensive"
        elif estimated_coverage > 0.4 or doc_example_count > 0:
            quality = "good"

        confidence = 0.85

        evidence = []
        for match in doc_examples[:ctx.max_evidence_snippets]:
            rel_path, line, _ = match
            ev = make_evidence(index, rel_path, line, radius=4)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.documentation",
            category="documentation",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "doc_comment_count": doc_comment_count,
                "module_doc_count": module_doc_count,
                "doc_example_count": doc_example_count,
                "total_pub_items": total_pub_items,
                "estimated_coverage": round(estimated_coverage, 2),
                "enforces_docs": enforces_docs,
                "warns_docs": warns_docs,
                "quality": quality,
            },
        ))

        return result
