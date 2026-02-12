"""Rust data flow detector.

Builds import graph, traces endpoint chains, and maps service dependencies.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..base import DetectorContext, DetectorResult
from ..graph import (
    FileNode,
    ImportEdge,
    build_import_graph,
    compute_summary,
    trace_endpoint_chains,
)
from ..registry import DetectorRegistry
from .base import RustDetector
from .index import RustIndex, make_evidence


def _resolve_use(
    importing_file: str,
    use_path: str,
    known_files: set[str],
) -> str | None:
    """Resolve a Rust use statement to a relative file path in the index.

    Args:
        importing_file: Relative path of the importing file.
        use_path: The use path (e.g., 'crate::services::user').
        known_files: Set of all indexed relative file paths.

    Returns:
        Resolved relative file path, or None if external/unresolvable.
    """
    # Only resolve crate-local imports
    if use_path.startswith("crate::"):
        # crate::services::user -> src/services/user.rs or src/services/user/mod.rs
        module_parts = use_path.split("::")[1:]  # skip "crate"
        if not module_parts:
            return None

        base_path = "src/" + "/".join(module_parts)

        # Try as file
        candidate = base_path + ".rs"
        if candidate in known_files:
            return candidate

        # Try as directory with mod.rs
        candidate = base_path + "/mod.rs"
        if candidate in known_files:
            return candidate

        # Try with fewer path components (the last part might be an item, not a module)
        if len(module_parts) > 1:
            base_path = "src/" + "/".join(module_parts[:-1])
            candidate = base_path + ".rs"
            if candidate in known_files:
                return candidate
            candidate = base_path + "/mod.rs"
            if candidate in known_files:
                return candidate

    elif use_path.startswith("super::"):
        # super:: -> parent module
        importing_dir = str(Path(importing_file).parent)
        parent_dir = str(Path(importing_dir).parent)
        module_parts = use_path.split("::")[1:]  # skip "super"
        if not module_parts:
            return None

        base_path = os.path.normpath(os.path.join(parent_dir, module_parts[0]))
        base_path = base_path.replace("\\", "/")

        candidate = base_path + ".rs"
        if candidate in known_files:
            return candidate
        candidate = base_path + "/mod.rs"
        if candidate in known_files:
            return candidate

    elif use_path.startswith("self::"):
        # self:: -> current module
        importing_dir = str(Path(importing_file).parent)
        module_parts = use_path.split("::")[1:]  # skip "self"
        if not module_parts:
            return None

        base_path = os.path.normpath(os.path.join(importing_dir, module_parts[0]))
        base_path = base_path.replace("\\", "/")

        candidate = base_path + ".rs"
        if candidate in known_files:
            return candidate
        candidate = base_path + "/mod.rs"
        if candidate in known_files:
            return candidate

    return None


@DetectorRegistry.register
class RustDataFlowDetector(RustDetector):
    """Detect Rust data flow patterns."""

    name = "rust_data_flow"
    description = "Detects Rust data flow: import graph, endpoint chains, service dependencies"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect data flow patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files or len(index.files) < 5:
            return result

        # Build graph from index
        nodes, edges = self._build_graph_from_index(index)
        if not edges:
            return result

        adj = build_import_graph(nodes, edges)

        # Emit import graph rule
        self._emit_import_graph_rule(ctx, index, nodes, edges, adj, result)

        # Emit endpoint chains rule
        self._emit_endpoint_chains_rule(ctx, index, nodes, adj, result)

        # Emit service dependencies rule
        self._emit_service_deps_rule(ctx, index, nodes, adj, result)

        return result

    def _build_graph_from_index(
        self,
        index: RustIndex,
    ) -> tuple[dict[str, FileNode], list[ImportEdge]]:
        """Build graph data structures from RustIndex."""
        known_files = set(index.files.keys())
        nodes: dict[str, FileNode] = {}
        edges: list[ImportEdge] = []

        for rel_path, file_idx in index.files.items():
            nodes[rel_path] = FileNode(path=rel_path, role=file_idx.role)

            for use_path, line in file_idx.uses:
                resolved = _resolve_use(rel_path, use_path, known_files)
                if resolved and resolved != rel_path:
                    edges.append(ImportEdge(
                        source=rel_path,
                        target=resolved,
                        line=line,
                        module_spec=use_path,
                    ))

        return nodes, edges

    def _emit_import_graph_rule(
        self,
        ctx: DetectorContext,
        index: RustIndex,
        nodes: dict[str, FileNode],
        edges: list[ImportEdge],
        adj: dict[str, list[str]],
        result: DetectorResult,
    ) -> None:
        """Emit the import graph summary rule."""
        summary = compute_summary(nodes, edges, adj)

        if summary.total_edges < 5:
            return

        cycle_count = len(summary.cycles)
        cluster_count = len(summary.clusters)

        cycle_desc = ""
        if cycle_count:
            cycle_files = [" -> ".join(c.cycle) for c in summary.cycles[:3]]
            cycle_desc = f" Circular dependencies: {cycle_count}. " + "; ".join(cycle_files) + "."

        description = (
            f"Import graph: {summary.total_files} files, {summary.total_edges} internal imports. "
            f"{cluster_count} dependency clusters."
            f"{cycle_desc}"
        )

        if summary.top_fan_in:
            top_imported = summary.top_fan_in[0]
            description += f" Most imported: {top_imported[0]} ({top_imported[1]} dependents)."

        confidence = min(0.90, 0.60 + summary.total_edges * 0.002)

        evidence = []
        for path, fan_in in summary.top_fan_in[:ctx.max_evidence_snippets]:
            if path in index.files:
                ev = make_evidence(index, path, 1, radius=3)
                if ev:
                    evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.data_flow.import_graph",
            category="data_flow",
            title="Import dependency graph",
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "total_files": summary.total_files,
                "total_edges": summary.total_edges,
                "cycle_count": cycle_count,
                "cluster_count": cluster_count,
                "top_fan_in": summary.top_fan_in[:5],
                "top_fan_out": summary.top_fan_out[:5],
            },
        ))

    def _emit_endpoint_chains_rule(
        self,
        ctx: DetectorContext,
        index: RustIndex,
        nodes: dict[str, FileNode],
        adj: dict[str, list[str]],
        result: DetectorResult,
    ) -> None:
        """Emit the endpoint chains rule."""
        api_files = [path for path, node in nodes.items() if node.role == "api"]
        if not api_files:
            return

        chains = trace_endpoint_chains(api_files, adj, nodes)
        if not chains:
            return

        chain_descs = []
        for chain in chains[:10]:
            parts = [chain.endpoint_file]
            if chain.service_files:
                parts.append(chain.service_files[0])
            if chain.store_files:
                parts.append(chain.store_files[0])
            chain_descs.append(" -> ".join(parts))

        description = (
            f"Traced {len(chains)} endpoint chains from API to service/store layers. "
            + "; ".join(chain_descs[:5])
        )

        confidence = min(0.90, 0.60 + len(chains) * 0.05)

        evidence = []
        for chain in chains[:ctx.max_evidence_snippets]:
            if chain.endpoint_file in index.files:
                ev = make_evidence(index, chain.endpoint_file, 1, radius=3)
                if ev:
                    evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.data_flow.endpoint_chains",
            category="data_flow",
            title="API endpoint chains",
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "chain_count": len(chains),
                "chains": [
                    {
                        "endpoint": c.endpoint_file,
                        "services": c.service_files,
                        "stores": c.store_files,
                        "depth": c.chain_depth,
                    }
                    for c in chains[:20]
                ],
            },
        ))

    def _emit_service_deps_rule(
        self,
        ctx: DetectorContext,
        index: RustIndex,
        nodes: dict[str, FileNode],
        adj: dict[str, list[str]],
        result: DetectorResult,
    ) -> None:
        """Emit the service dependencies rule."""
        service_files = [path for path, node in nodes.items() if node.role == "service"]
        if not service_files:
            return

        deps: dict[str, list[str]] = {}
        for svc_file in service_files:
            store_deps = []
            for target in adj.get(svc_file, []):
                if target in nodes and nodes[target].role == "db":
                    store_deps.append(target)
            if store_deps:
                deps[svc_file] = sorted(store_deps)

        if not deps:
            return

        dep_descs = []
        for svc, stores in list(deps.items())[:5]:
            dep_descs.append(f"{svc} -> {', '.join(stores)}")

        description = (
            f"{len(deps)} services with store/db dependencies. "
            + "; ".join(dep_descs)
        )

        confidence = min(0.90, 0.60 + len(deps) * 0.05)

        result.rules.append(self.make_rule(
            rule_id="rust.data_flow.service_dependencies",
            category="data_flow",
            title="Service dependency map",
            description=description,
            confidence=confidence,
            language="rust",
            evidence=[],
            stats={
                "dependency_count": len(deps),
                "dependencies": deps,
            },
        ))
