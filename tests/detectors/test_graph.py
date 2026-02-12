"""Tests for shared graph utilities."""
from __future__ import annotations

from conventions.detectors.graph import (
    CircularDependency,
    DependencyCluster,
    EndpointChain,
    FileNode,
    ImportEdge,
    ImportGraphSummary,
    build_import_graph,
    compute_summary,
    find_clusters,
    find_cycles,
    trace_endpoint_chains,
)


def _make_nodes(*specs: tuple[str, str]) -> dict[str, FileNode]:
    """Create FileNode dict from (path, role) tuples."""
    return {path: FileNode(path=path, role=role) for path, role in specs}


def _make_edges(*specs: tuple[str, str, str]) -> list[ImportEdge]:
    """Create ImportEdge list from (source, target, module_spec) tuples."""
    return [
        ImportEdge(source=s, target=t, line=1, module_spec=m)
        for s, t, m in specs
    ]


class TestBuildImportGraph:
    """Tests for build_import_graph."""

    def test_builds_adjacency_list(self):
        nodes = _make_nodes(("a.ts", "api"), ("b.ts", "service"), ("c.ts", "db"))
        edges = _make_edges(("a.ts", "b.ts", "./b"), ("b.ts", "c.ts", "./c"))
        adj = build_import_graph(nodes, edges)

        assert adj["a.ts"] == ["b.ts"]
        assert adj["b.ts"] == ["c.ts"]

    def test_computes_fan_in_fan_out(self):
        nodes = _make_nodes(("a.ts", "api"), ("b.ts", "service"), ("c.ts", "db"))
        edges = _make_edges(
            ("a.ts", "b.ts", "./b"),
            ("a.ts", "c.ts", "./c"),
            ("b.ts", "c.ts", "./c"),
        )
        build_import_graph(nodes, edges)

        assert nodes["a.ts"].fan_out == 2
        assert nodes["a.ts"].fan_in == 0
        assert nodes["b.ts"].fan_out == 1
        assert nodes["b.ts"].fan_in == 1
        assert nodes["c.ts"].fan_out == 0
        assert nodes["c.ts"].fan_in == 2

    def test_skips_edges_with_unknown_nodes(self):
        nodes = _make_nodes(("a.ts", "api"))
        edges = _make_edges(("a.ts", "unknown.ts", "./unknown"))
        adj = build_import_graph(nodes, edges)

        assert "a.ts" not in adj or "unknown.ts" not in adj.get("a.ts", [])

    def test_deduplicates_edges(self):
        nodes = _make_nodes(("a.ts", "api"), ("b.ts", "service"))
        edges = _make_edges(
            ("a.ts", "b.ts", "./b"),
            ("a.ts", "b.ts", "./b"),  # duplicate
        )
        adj = build_import_graph(nodes, edges)
        assert len(adj["a.ts"]) == 1

    def test_empty_graph(self):
        nodes: dict[str, FileNode] = {}
        edges: list[ImportEdge] = []
        adj = build_import_graph(nodes, edges)
        assert adj == {}


class TestFindCycles:
    """Tests for find_cycles."""

    def test_detects_simple_cycle(self):
        adj = {"a": ["b"], "b": ["c"], "c": ["a"]}
        cycles = find_cycles(adj)

        assert len(cycles) >= 1
        # The cycle a->b->c should be found
        cycle_sets = [set(c.cycle) for c in cycles]
        assert {"a", "b", "c"} in cycle_sets

    def test_no_cycle_in_acyclic_graph(self):
        adj = {"a": ["b"], "b": ["c"]}
        cycles = find_cycles(adj)
        assert len(cycles) == 0

    def test_detects_self_loop(self):
        adj = {"a": ["a"]}
        cycles = find_cycles(adj)
        assert len(cycles) >= 1

    def test_detects_two_node_cycle(self):
        adj = {"a": ["b"], "b": ["a"]}
        cycles = find_cycles(adj)
        assert len(cycles) >= 1
        cycle_sets = [set(c.cycle) for c in cycles]
        assert {"a", "b"} in cycle_sets

    def test_respects_max_length(self):
        # Create a cycle of length 4: a->b->c->d->a
        adj = {"a": ["b"], "b": ["c"], "c": ["d"], "d": ["a"]}
        cycles = find_cycles(adj, max_length=3)
        # Cycle length 4 should be excluded when max_length=3
        assert len(cycles) == 0

    def test_respects_max_results(self):
        # Create many small cycles
        adj: dict[str, list[str]] = {}
        for i in range(30):
            a, b = f"a{i}", f"b{i}"
            adj[a] = [b]
            adj[b] = [a]
        cycles = find_cycles(adj, max_results=5)
        assert len(cycles) <= 5

    def test_empty_graph(self):
        cycles = find_cycles({})
        assert cycles == []


class TestFindClusters:
    """Tests for find_clusters."""

    def test_finds_connected_component(self):
        adj = {
            "a": ["b"],
            "b": ["c"],
            "c": ["a"],
        }
        clusters = find_clusters(adj, min_size=2)
        assert len(clusters) >= 1
        assert set(clusters[0].files) == {"a", "b", "c"}

    def test_finds_separate_components(self):
        adj = {
            "a": ["b"],
            "b": ["a"],
            "c": ["d"],
            "d": ["c"],
            "e": ["f"],
            "f": ["e"],
        }
        clusters = find_clusters(adj, min_size=2)
        assert len(clusters) == 3

    def test_filters_by_min_size(self):
        adj = {"a": ["b"], "b": ["a"]}
        clusters = find_clusters(adj, min_size=3)
        assert len(clusters) == 0

    def test_computes_cohesion(self):
        # 3-node cycle: 3 directed edges out of max 6 possible
        adj = {"a": ["b"], "b": ["c"], "c": ["a"]}
        clusters = find_clusters(adj, min_size=2)
        assert len(clusters) == 1
        assert clusters[0].internal_edges == 3
        assert clusters[0].cohesion == 0.5  # 3 / (3*2)

    def test_empty_graph(self):
        clusters = find_clusters({})
        assert clusters == []


class TestComputeSummary:
    """Tests for compute_summary."""

    def test_basic_summary(self):
        nodes = _make_nodes(
            ("a.ts", "api"),
            ("b.ts", "service"),
            ("c.ts", "db"),
        )
        edges = _make_edges(
            ("a.ts", "b.ts", "./b"),
            ("b.ts", "c.ts", "./c"),
        )
        adj = build_import_graph(nodes, edges)
        summary = compute_summary(nodes, edges, adj)

        assert summary.total_files == 3
        assert summary.total_edges == 2
        assert isinstance(summary.clusters, list)
        assert isinstance(summary.cycles, list)

    def test_top_fan_in(self):
        nodes = _make_nodes(
            ("a.ts", "api"),
            ("b.ts", "api"),
            ("c.ts", "service"),
        )
        edges = _make_edges(
            ("a.ts", "c.ts", "./c"),
            ("b.ts", "c.ts", "./c"),
        )
        adj = build_import_graph(nodes, edges)
        summary = compute_summary(nodes, edges, adj)

        assert summary.top_fan_in[0] == ("c.ts", 2)


class TestTraceEndpointChains:
    """Tests for trace_endpoint_chains."""

    def test_traces_api_service_db_chain(self):
        nodes = _make_nodes(
            ("routes/users.ts", "api"),
            ("services/user.ts", "service"),
            ("stores/user.ts", "db"),
        )
        adj = {
            "routes/users.ts": ["services/user.ts"],
            "services/user.ts": ["stores/user.ts"],
        }

        chains = trace_endpoint_chains(["routes/users.ts"], adj, nodes)
        assert len(chains) == 1
        chain = chains[0]
        assert chain.endpoint_file == "routes/users.ts"
        assert "services/user.ts" in chain.service_files
        assert "stores/user.ts" in chain.store_files
        assert chain.chain_depth == 3

    def test_api_direct_to_db(self):
        nodes = _make_nodes(
            ("routes/users.ts", "api"),
            ("stores/user.ts", "db"),
        )
        adj = {"routes/users.ts": ["stores/user.ts"]}

        chains = trace_endpoint_chains(["routes/users.ts"], adj, nodes)
        assert len(chains) == 1
        assert chains[0].service_files == []
        assert "stores/user.ts" in chains[0].store_files
        assert chains[0].chain_depth == 2

    def test_no_chain_when_only_test_deps(self):
        nodes = _make_nodes(
            ("routes/users.ts", "api"),
            ("tests/user.test.ts", "test"),
        )
        adj = {"routes/users.ts": ["tests/user.test.ts"]}

        chains = trace_endpoint_chains(["routes/users.ts"], adj, nodes)
        assert len(chains) == 0

    def test_respects_max_depth(self):
        nodes = _make_nodes(
            ("a.ts", "api"),
            ("b.ts", "other"),
            ("c.ts", "other"),
            ("d.ts", "other"),
            ("e.ts", "service"),
        )
        adj = {
            "a.ts": ["b.ts"],
            "b.ts": ["c.ts"],
            "c.ts": ["d.ts"],
            "d.ts": ["e.ts"],
        }

        # max_depth=2 should not reach e.ts through 4 hops
        chains = trace_endpoint_chains(["a.ts"], adj, nodes, max_depth=2)
        if chains:
            assert "e.ts" not in chains[0].service_files

    def test_empty_endpoint_list(self):
        chains = trace_endpoint_chains([], {}, {})
        assert chains == []

    def test_multiple_endpoints(self):
        nodes = _make_nodes(
            ("routes/users.ts", "api"),
            ("routes/posts.ts", "api"),
            ("services/user.ts", "service"),
            ("services/post.ts", "service"),
        )
        adj = {
            "routes/users.ts": ["services/user.ts"],
            "routes/posts.ts": ["services/post.ts"],
        }

        chains = trace_endpoint_chains(
            ["routes/users.ts", "routes/posts.ts"], adj, nodes
        )
        assert len(chains) == 2
