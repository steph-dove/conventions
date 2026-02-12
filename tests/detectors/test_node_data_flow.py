"""Integration tests for Node.js data flow detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext, DetectorResult
from conventions.detectors.node.data_flow import NodeDataFlowDetector


@pytest.fixture
def node_repo(tmp_path: Path) -> Path:
    """Create a Node.js repo with layered architecture."""
    # Route file
    routes = tmp_path / "src" / "routes"
    routes.mkdir(parents=True)
    (routes / "users.ts").write_text(
        'import { UserService } from "../services/userService";\n'
        'import express from "express";\n'
        "const router = express.Router();\n"
        'router.get("/users", async (req, res) => {\n'
        "  const svc = new UserService();\n"
        "  res.json(await svc.getAll());\n"
        "});\n"
        "export default router;\n"
    )
    (routes / "posts.ts").write_text(
        'import { PostService } from "../services/postService";\n'
        'import express from "express";\n'
        "const router = express.Router();\n"
        'router.get("/posts", async (req, res) => {\n'
        "  res.json([]);\n"
        "});\n"
        "export default router;\n"
    )

    # Service files
    services = tmp_path / "src" / "services"
    services.mkdir(parents=True)
    (services / "userService.ts").write_text(
        'import { UserStore } from "../store/userStore";\n'
        'import { log } from "../utils/logger";\n'
        "export class UserService {\n"
        "  private store = new UserStore();\n"
        '  async getAll() { log("getAll"); return this.store.findAll(); }\n'
        "}\n"
    )
    (services / "postService.ts").write_text(
        'import { PostStore } from "../store/postStore";\n'
        'import { log } from "../utils/logger";\n'
        "export class PostService {\n"
        "  private store = new PostStore();\n"
        '  async getAll() { log("getAll"); return this.store.findAll(); }\n'
        "}\n"
    )

    # Store files
    store = tmp_path / "src" / "store"
    store.mkdir(parents=True)
    (store / "userStore.ts").write_text(
        "export class UserStore {\n"
        '  async findAll() { return [{ id: 1, name: "Alice" }]; }\n'
        "}\n"
    )
    (store / "postStore.ts").write_text(
        "export class PostStore {\n"
        "  async findAll() { return []; }\n"
        "}\n"
    )

    # Utility file (to pad out the graph)
    utils = tmp_path / "src" / "utils"
    utils.mkdir(parents=True)
    (utils / "logger.ts").write_text(
        'export function log(msg: string) { console.log(msg); }\n'
    )

    # package.json
    (tmp_path / "package.json").write_text('{"name": "test", "version": "1.0.0"}')

    return tmp_path


@pytest.fixture
def circular_repo(tmp_path: Path) -> Path:
    """Create a repo with circular imports."""
    src = tmp_path / "src"
    src.mkdir()

    (src / "a.ts").write_text('import { b } from "./b";\nexport const a = 1;\n')
    (src / "b.ts").write_text('import { c } from "./c";\nexport const b = 2;\n')
    (src / "c.ts").write_text('import { a } from "./a";\nexport const c = 3;\n')
    (src / "d.ts").write_text('import { a } from "./a";\nexport const d = 4;\n')
    (src / "e.ts").write_text('import { d } from "./d";\nexport const e = 5;\n')

    (tmp_path / "package.json").write_text('{"name": "test", "version": "1.0.0"}')
    return tmp_path


class TestNodeDataFlowDetector:
    """Tests for NodeDataFlowDetector."""

    def test_detects_import_graph(self, node_repo: Path):
        """Detects import graph with correct stats."""
        ctx = DetectorContext(
            repo_root=node_repo,
            selected_languages={"node"},
            max_files=100,
        )
        detector = NodeDataFlowDetector()
        result = detector.detect(ctx)

        graph_rules = [r for r in result.rules if r.id == "node.data_flow.import_graph"]
        assert len(graph_rules) == 1
        rule = graph_rules[0]
        assert rule.stats["total_files"] >= 6
        assert rule.stats["total_edges"] >= 4

    def test_detects_endpoint_chains(self, node_repo: Path):
        """Traces endpoint chains from routes to stores."""
        ctx = DetectorContext(
            repo_root=node_repo,
            selected_languages={"node"},
            max_files=100,
        )
        detector = NodeDataFlowDetector()
        result = detector.detect(ctx)

        chain_rules = [r for r in result.rules if r.id == "node.data_flow.endpoint_chains"]
        assert len(chain_rules) == 1
        rule = chain_rules[0]
        assert rule.stats["chain_count"] >= 2

        # Verify chains go through service and store layers
        chains = rule.stats["chains"]
        user_chain = [c for c in chains if "routes/users.ts" in c["endpoint"]]
        assert len(user_chain) >= 1
        assert len(user_chain[0]["services"]) >= 1
        assert len(user_chain[0]["stores"]) >= 1

    def test_detects_service_dependencies(self, node_repo: Path):
        """Maps service to store dependencies."""
        ctx = DetectorContext(
            repo_root=node_repo,
            selected_languages={"node"},
            max_files=100,
        )
        detector = NodeDataFlowDetector()
        result = detector.detect(ctx)

        dep_rules = [r for r in result.rules if r.id == "node.data_flow.service_dependencies"]
        assert len(dep_rules) == 1
        assert dep_rules[0].stats["dependency_count"] >= 2

    def test_detects_circular_dependencies(self, circular_repo: Path):
        """Reports circular dependencies in import graph."""
        ctx = DetectorContext(
            repo_root=circular_repo,
            selected_languages={"node"},
            max_files=100,
        )
        detector = NodeDataFlowDetector()
        result = detector.detect(ctx)

        graph_rules = [r for r in result.rules if r.id == "node.data_flow.import_graph"]
        assert len(graph_rules) == 1
        assert graph_rules[0].stats["cycle_count"] >= 1

    def test_no_rules_on_empty_repo(self, tmp_path: Path):
        """No rules emitted for empty repo."""
        (tmp_path / "package.json").write_text('{"name": "empty"}')
        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"node"},
            max_files=100,
        )
        detector = NodeDataFlowDetector()
        result = detector.detect(ctx)
        assert len(result.rules) == 0
