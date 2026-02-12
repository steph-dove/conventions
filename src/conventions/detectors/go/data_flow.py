"""Go data flow detector.

Builds import graph, traces endpoint chains, and maps service dependencies.
"""

from __future__ import annotations

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
from .base import GoDetector
from .index import GoIndex, make_evidence


def _read_go_module(repo_root: Path) -> str | None:
    """Read the module path from go.mod."""
    go_mod = repo_root / "go.mod"
    if not go_mod.exists():
        return None
    try:
        content = go_mod.read_text(errors="replace")
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("module "):
                return line.split(None, 1)[1].strip()
    except OSError:
        pass
    return None


def _resolve_import(
    module_prefix: str | None,
    import_path: str,
    known_dirs: set[str],
) -> str | None:
    """Resolve a Go import path to a directory in the index.

    Go imports reference packages (directories), not individual files.
    We match the import suffix against known directory paths.

    Args:
        module_prefix: The module path from go.mod (e.g., 'github.com/user/project').
        import_path: The import string (e.g., 'github.com/user/project/internal/service').
        known_dirs: Set of all known package directories (relative paths).

    Returns:
        Resolved relative directory path, or None if external/unresolvable.
    """
    if module_prefix and import_path.startswith(module_prefix):
        # Strip module prefix to get relative path
        rel = import_path[len(module_prefix):]
        if rel.startswith("/"):
            rel = rel[1:]
        if rel in known_dirs:
            return rel
    return None


@DetectorRegistry.register
class GoDataFlowDetector(GoDetector):
    """Detect Go data flow patterns."""

    name = "go_data_flow"
    description = "Detects Go data flow: import graph, endpoint chains, service dependencies"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect data flow patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files or len(index.files) < 5:
            return result

        module_prefix = _read_go_module(ctx.repo_root)

        # Build graph from index
        nodes, edges = self._build_graph_from_index(index, module_prefix)
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
        index: GoIndex,
        module_prefix: str | None,
    ) -> tuple[dict[str, FileNode], list[ImportEdge]]:
        """Build graph data structures from GoIndex.

        Go imports reference packages (directories), so we group files by
        directory and create edges between directories.
        """
        # Build directory -> role mapping from files
        dir_roles: dict[str, str] = {}
        for rel_path, file_idx in index.files.items():
            dir_path = str(Path(rel_path).parent)
            # Use the first non-test, non-other role found
            if dir_path not in dir_roles or dir_roles[dir_path] == "other":
                dir_roles[dir_path] = file_idx.role

        known_dirs = set(dir_roles.keys())

        # Create nodes per directory
        nodes: dict[str, FileNode] = {}
        for dir_path, role in dir_roles.items():
            nodes[dir_path] = FileNode(path=dir_path, role=role)

        # Create edges between directories
        edges: list[ImportEdge] = []
        seen_edges: set[tuple[str, str]] = set()

        for rel_path, file_idx in index.files.items():
            source_dir = str(Path(rel_path).parent)

            for import_path, line in file_idx.imports:
                target_dir = _resolve_import(module_prefix, import_path, known_dirs)
                if target_dir and target_dir != source_dir:
                    edge_key = (source_dir, target_dir)
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges.append(ImportEdge(
                            source=source_dir,
                            target=target_dir,
                            line=line,
                            module_spec=import_path,
                        ))

        return nodes, edges

    def _emit_import_graph_rule(
        self,
        ctx: DetectorContext,
        index: GoIndex,
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
            f"Import graph: {summary.total_files} packages, {summary.total_edges} internal imports. "
            f"{cluster_count} dependency clusters."
            f"{cycle_desc}"
        )

        if summary.top_fan_in:
            top_imported = summary.top_fan_in[0]
            description += f" Most imported: {top_imported[0]} ({top_imported[1]} dependents)."

        confidence = min(0.90, 0.60 + summary.total_edges * 0.002)

        # Evidence: top fan-in directories - pick a representative file
        evidence = []
        for path, fan_in in summary.top_fan_in[:ctx.max_evidence_snippets]:
            # Find a file in this directory
            for rel_path in index.files:
                if str(Path(rel_path).parent) == path:
                    ev = make_evidence(index, rel_path, 1, radius=3)
                    if ev:
                        evidence.append(ev)
                    break

        result.rules.append(self.make_rule(
            rule_id="go.data_flow.import_graph",
            category="data_flow",
            title="Import dependency graph",
            description=description,
            confidence=confidence,
            language="go",
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
        index: GoIndex,
        nodes: dict[str, FileNode],
        adj: dict[str, list[str]],
        result: DetectorResult,
    ) -> None:
        """Emit the endpoint chains rule."""
        api_dirs = [n for n, node in nodes.items() if node.role == "api"]
        if not api_dirs:
            return

        chains = trace_endpoint_chains(api_dirs, adj, nodes)
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
            for rel_path in index.files:
                if str(Path(rel_path).parent) == chain.endpoint_file:
                    ev = make_evidence(index, rel_path, 1, radius=3)
                    if ev:
                        evidence.append(ev)
                    break

        result.rules.append(self.make_rule(
            rule_id="go.data_flow.endpoint_chains",
            category="data_flow",
            title="API endpoint chains",
            description=description,
            confidence=confidence,
            language="go",
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
        index: GoIndex,
        nodes: dict[str, FileNode],
        adj: dict[str, list[str]],
        result: DetectorResult,
    ) -> None:
        """Emit the service dependencies rule."""
        service_dirs = [n for n, node in nodes.items() if node.role == "service"]
        if not service_dirs:
            return

        deps: dict[str, list[str]] = {}
        for svc_dir in service_dirs:
            store_deps = []
            for target in adj.get(svc_dir, []):
                if target in nodes and nodes[target].role == "db":
                    store_deps.append(target)
            if store_deps:
                deps[svc_dir] = sorted(store_deps)

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
            rule_id="go.data_flow.service_dependencies",
            category="data_flow",
            title="Service dependency map",
            description=description,
            confidence=confidence,
            language="go",
            evidence=[],
            stats={
                "dependency_count": len(deps),
                "dependencies": deps,
            },
        ))
