"""Rust macro usage conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import RustDetector
from .index import make_evidence


@DetectorRegistry.register
class RustMacrosDetector(RustDetector):
    """Detect Rust macro conventions."""

    name = "rust_macros"
    description = "Analyzes macro usage and proc-macro patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect macro conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Count macro_rules! definitions
        macro_rules_count = 0
        macro_names = []
        for file_idx in index.get_non_test_files():
            for name, _ in file_idx.macros:
                macro_rules_count += 1
                macro_names.append(name)

        # Check for proc-macro crate
        cargo_toml = ctx.repo_root / "Cargo.toml"
        is_proc_macro = False
        if cargo_toml.exists():
            content = cargo_toml.read_text()
            is_proc_macro = "proc-macro = true" in content

        # Check for derive macros usage
        derive_usage = index.search_pattern(
            r"#\[derive\([^\)]+\)\]",
            limit=100,
            exclude_tests=True,
        )

        # Common derive traits
        derive_traits: dict[str, int] = {}
        for _, _, match in derive_usage:
            # Extract traits from derive
            import re
            traits = re.findall(r"(\w+)", match.replace("#[derive(", "").replace(")]", ""))
            for trait in traits:
                derive_traits[trait] = derive_traits.get(trait, 0) + 1

        # Check for attribute macros usage
        attr_macros = index.search_pattern(
            r"#\[(?:tokio::main|tokio::test|async_trait|instrument|tracing::instrument)\]",
            limit=50,
            exclude_tests=True,
        )

        # Check for proc-macro libraries
        proc_macro_libs: dict[str, int] = {}

        # syn
        syn_uses = index.find_uses_matching("syn", limit=20)
        if syn_uses:
            proc_macro_libs["syn"] = len(syn_uses)

        # quote
        quote_uses = index.find_uses_matching("quote", limit=20)
        if quote_uses:
            proc_macro_libs["quote"] = len(quote_uses)

        # proc-macro2
        pm2_uses = index.find_uses_matching("proc_macro2", limit=20)
        if pm2_uses:
            proc_macro_libs["proc_macro2"] = len(pm2_uses)

        # darling
        darling_uses = index.find_uses_matching("darling", limit=20)
        if darling_uses:
            proc_macro_libs["darling"] = len(darling_uses)

        if macro_rules_count == 0 and not is_proc_macro and len(derive_usage) < 10:
            return result

        examples: list[tuple[str, int]] = []

        # Get top derives
        top_derives = sorted(derive_traits.items(), key=lambda x: -x[1])[:5]
        top_derive_names = [t[0] for t in top_derives]

        if is_proc_macro:
            title = "Macros: Proc-macro crate"
            description = "This is a proc-macro crate."
            if proc_macro_libs:
                description += f" Uses: {', '.join(proc_macro_libs.keys())}."
        elif macro_rules_count > 0:
            title = f"Macros: {macro_rules_count} macro_rules!"
            description = f"Defines {macro_rules_count} declarative macro(s)."
            if macro_names[:3]:
                description += f" Including: {', '.join(macro_names[:3])}."
        else:
            title = f"Macros: {len(derive_usage)} derive usages"
            description = "Uses derive macros extensively."

        if top_derive_names and not is_proc_macro:
            description += f" Common derives: {', '.join(top_derive_names[:4])}."

        if len(attr_macros) > 0 and not is_proc_macro:
            description += f" {len(attr_macros)} attribute macro usage(s)."

        confidence = 0.85

        # Get examples from macro definitions
        for file_idx in index.get_non_test_files():
            for name, line in file_idx.macros[:3]:
                examples.append((file_idx.relative_path, line))

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=4)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.macros",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "macro_rules_count": macro_rules_count,
                "is_proc_macro": is_proc_macro,
                "derive_usage_count": len(derive_usage),
                "top_derives": top_derive_names,
                "proc_macro_libs": list(proc_macro_libs.keys()),
                "macro_names": macro_names[:10],
            },
        ))

        return result
