"""Shared graph utilities for data flow analysis.

Language-agnostic data structures and algorithms for import graph analysis,
cycle detection, clustering, and endpoint chain tracing.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class ImportEdge:
    """A directed edge in the import graph."""

    source: str  # relative file path (importer)
    target: str  # relative file path (imported)
    line: int
    module_spec: str  # raw import string


@dataclass
class FileNode:
    """A node in the import graph."""

    path: str
    role: str  # api, service, db, test, other
    fan_in: int = 0
    fan_out: int = 0


@dataclass
class CircularDependency:
    """A cycle in the import graph."""

    cycle: list[str]  # ordered file paths forming the cycle


@dataclass
class DependencyCluster:
    """A group of tightly coupled files."""

    files: list[str]
    internal_edges: int
    cohesion: float  # internal_edges / total possible internal edges


@dataclass
class EndpointChain:
    """A traced endpoint-to-store chain."""

    endpoint_file: str
    endpoint_line: int
    endpoint_spec: str  # e.g. "GET /api/users"
    handler_file: str
    handler_name: str
    service_files: list[str] = field(default_factory=list)
    store_files: list[str] = field(default_factory=list)
    chain_depth: int = 1


@dataclass
class ImportGraphSummary:
    """Summary of import graph analysis."""

    total_files: int
    total_edges: int
    clusters: list[DependencyCluster]
    cycles: list[CircularDependency]
    top_fan_in: list[tuple[str, int]]  # top N files by fan-in
    top_fan_out: list[tuple[str, int]]  # top N files by fan-out


def build_import_graph(
    nodes: dict[str, FileNode],
    edges: list[ImportEdge],
) -> dict[str, list[str]]:
    """Build adjacency list from edges and compute fan-in/fan-out.

    Mutates FileNode.fan_in and FileNode.fan_out in place.

    Returns:
        Adjacency list mapping source path -> list of target paths.
    """
    adj: dict[str, list[str]] = defaultdict(list)

    for edge in edges:
        if edge.source in nodes and edge.target in nodes:
            if edge.target not in adj[edge.source]:
                adj[edge.source].append(edge.target)

    # Compute fan-in/fan-out
    for node in nodes.values():
        node.fan_in = 0
        node.fan_out = 0

    for source, targets in adj.items():
        if source in nodes:
            nodes[source].fan_out = len(targets)
        for target in targets:
            if target in nodes:
                nodes[target].fan_in += 1

    return dict(adj)


def find_cycles(
    adj: dict[str, list[str]],
    max_length: int = 6,
    max_results: int = 20,
) -> list[CircularDependency]:
    """Find cycles in the import graph using DFS.

    Args:
        adj: Adjacency list.
        max_length: Maximum cycle length to report.
        max_results: Maximum number of cycles to return.

    Returns:
        List of CircularDependency objects, shortest first.
    """
    cycles: list[list[str]] = []
    visited: set[str] = set()

    def _dfs(node: str, path: list[str], path_set: set[str]) -> None:
        if len(cycles) >= max_results * 2:  # collect extra, dedupe later
            return
        if len(path) > max_length:
            return

        for neighbor in adj.get(node, []):
            if neighbor in path_set:
                # Found a cycle - extract it
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                if len(cycle) - 1 <= max_length:  # -1 because last == first
                    cycles.append(cycle)
                continue

            if neighbor not in visited:
                path.append(neighbor)
                path_set.add(neighbor)
                _dfs(neighbor, path, path_set)
                path.pop()
                path_set.discard(neighbor)

    all_nodes = set(adj.keys())
    for targets in adj.values():
        all_nodes.update(targets)

    for node in sorted(all_nodes):
        if node not in visited:
            _dfs(node, [node], {node})
            visited.add(node)

    # Deduplicate cycles (same cycle can be found starting from different nodes)
    seen: set[tuple[str, ...]] = set()
    unique_cycles: list[CircularDependency] = []

    for cycle in sorted(cycles, key=len):
        # Normalize: rotate so smallest element is first
        loop = cycle[:-1]  # remove duplicate last element
        if not loop:
            continue
        min_idx = loop.index(min(loop))
        normalized = tuple(loop[min_idx:] + loop[:min_idx])
        if normalized not in seen:
            seen.add(normalized)
            unique_cycles.append(CircularDependency(cycle=list(normalized)))
            if len(unique_cycles) >= max_results:
                break

    return unique_cycles


def find_clusters(
    adj: dict[str, list[str]],
    min_size: int = 3,
) -> list[DependencyCluster]:
    """Find clusters of tightly coupled files using connected components.

    Builds an undirected projection of the graph and finds connected
    components, then scores each by cohesion.

    Args:
        adj: Adjacency list (directed).
        min_size: Minimum cluster size to report.

    Returns:
        List of DependencyCluster objects sorted by size descending.
    """
    # Build undirected adjacency
    undirected: dict[str, set[str]] = defaultdict(set)
    for source, targets in adj.items():
        for target in targets:
            undirected[source].add(target)
            undirected[target].add(source)

    # Find connected components via BFS
    visited: set[str] = set()
    components: list[list[str]] = []

    all_nodes = set(undirected.keys())
    for node in sorted(all_nodes):
        if node in visited:
            continue
        component: list[str] = []
        queue = [node]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            for neighbor in undirected.get(current, set()):
                if neighbor not in visited:
                    queue.append(neighbor)
        if len(component) >= min_size:
            components.append(sorted(component))

    # Score each component
    clusters: list[DependencyCluster] = []
    for component in components:
        component_set = set(component)
        internal_edges = 0
        for source in component:
            for target in adj.get(source, []):
                if target in component_set:
                    internal_edges += 1

        n = len(component)
        max_possible = n * (n - 1)  # directed graph max edges
        cohesion = internal_edges / max_possible if max_possible > 0 else 0.0

        clusters.append(DependencyCluster(
            files=component,
            internal_edges=internal_edges,
            cohesion=round(cohesion, 3),
        ))

    return sorted(clusters, key=lambda c: len(c.files), reverse=True)


def compute_summary(
    nodes: dict[str, FileNode],
    edges: list[ImportEdge],
    adj: dict[str, list[str]],
    top_n: int = 10,
) -> ImportGraphSummary:
    """Compute full import graph summary.

    Call build_import_graph() first to populate fan-in/fan-out on nodes.

    Args:
        nodes: File nodes with fan-in/fan-out already computed.
        edges: Import edges.
        adj: Adjacency list from build_import_graph().
        top_n: Number of top files to include in fan-in/fan-out lists.

    Returns:
        ImportGraphSummary with clusters, cycles, and coupling metrics.
    """
    cycles = find_cycles(adj)
    clusters = find_clusters(adj)

    # Top fan-in (most imported files)
    by_fan_in = sorted(
        [(n.path, n.fan_in) for n in nodes.values() if n.fan_in > 0],
        key=lambda x: x[1],
        reverse=True,
    )[:top_n]

    # Top fan-out (files that import the most)
    by_fan_out = sorted(
        [(n.path, n.fan_out) for n in nodes.values() if n.fan_out > 0],
        key=lambda x: x[1],
        reverse=True,
    )[:top_n]

    return ImportGraphSummary(
        total_files=len(nodes),
        total_edges=len(edges),
        clusters=clusters,
        cycles=cycles,
        top_fan_in=by_fan_in,
        top_fan_out=by_fan_out,
    )


def trace_endpoint_chains(
    endpoint_files: list[str],
    adj: dict[str, list[str]],
    nodes: dict[str, FileNode],
    max_depth: int = 4,
) -> list[EndpointChain]:
    """Trace chains from API endpoint files through service to store layers.

    Uses role-guided BFS: from api-role files, follows edges to service-role
    files, then to db-role files.

    Args:
        endpoint_files: List of file paths classified as API endpoints.
        adj: Import adjacency list.
        nodes: File nodes with roles.
        max_depth: Maximum chain depth.

    Returns:
        List of EndpointChain objects.
    """
    chains: list[EndpointChain] = []

    for ep_file in endpoint_files:
        if ep_file not in nodes:
            continue

        service_files: list[str] = []
        store_files: list[str] = []

        # BFS from endpoint file
        visited: set[str] = {ep_file}
        queue: list[tuple[str, int]] = [(ep_file, 0)]

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            for target in adj.get(current, []):
                if target in visited or target not in nodes:
                    continue
                visited.add(target)

                target_role = nodes[target].role
                if target_role == "service":
                    service_files.append(target)
                    queue.append((target, depth + 1))
                elif target_role == "db":
                    store_files.append(target)
                    # Don't continue past db layer
                elif target_role not in ("test",):
                    # Follow "other" role files (utilities, etc.)
                    queue.append((target, depth + 1))

        if service_files or store_files:
            depth = 1
            if service_files:
                depth += 1
            if store_files:
                depth += 1

            chains.append(EndpointChain(
                endpoint_file=ep_file,
                endpoint_line=0,
                endpoint_spec="",
                handler_file=ep_file,
                handler_name="",
                service_files=sorted(service_files),
                store_files=sorted(store_files),
                chain_depth=depth,
            ))

    return chains
