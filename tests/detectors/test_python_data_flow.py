"""Integration tests for Python data flow detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext, DetectorResult
from conventions.detectors.python.data_flow import PythonDataFlowDetector


@pytest.fixture
def python_repo(tmp_path: Path) -> Path:
    """Create a Python repo with layered architecture."""
    # API/routes
    api = tmp_path / "app" / "api"
    api.mkdir(parents=True)
    (api / "__init__.py").write_text("")
    (api / "users.py").write_text(
        "from app.services.user_service import UserService\n"
        "from fastapi import APIRouter\n"
        "\n"
        "router = APIRouter()\n"
        "\n"
        "@router.get('/users')\n"
        "async def get_users():\n"
        "    svc = UserService()\n"
        "    return await svc.get_all()\n"
    )
    (api / "posts.py").write_text(
        "from app.services.post_service import PostService\n"
        "from fastapi import APIRouter\n"
        "\n"
        "router = APIRouter()\n"
        "\n"
        "@router.get('/posts')\n"
        "async def get_posts():\n"
        "    svc = PostService()\n"
        "    return await svc.get_all()\n"
    )

    # Services
    services = tmp_path / "app" / "services"
    services.mkdir(parents=True)
    (services / "__init__.py").write_text("")
    (services / "user_service.py").write_text(
        "from app.db.user_repo import UserRepo\n"
        "from app.utils.logger import get_logger\n"
        "\n"
        "logger = get_logger(__name__)\n"
        "\n"
        "class UserService:\n"
        "    def __init__(self):\n"
        "        self.repo = UserRepo()\n"
        "    async def get_all(self):\n"
        "        return await self.repo.find_all()\n"
    )
    (services / "post_service.py").write_text(
        "from app.db.post_repo import PostRepo\n"
        "from app.utils.logger import get_logger\n"
        "\n"
        "logger = get_logger(__name__)\n"
        "\n"
        "class PostService:\n"
        "    def __init__(self):\n"
        "        self.repo = PostRepo()\n"
        "    async def get_all(self):\n"
        "        return await self.repo.find_all()\n"
    )

    # DB/repositories
    db = tmp_path / "app" / "db"
    db.mkdir(parents=True)
    (db / "__init__.py").write_text("")
    (db / "user_repo.py").write_text(
        "class UserRepo:\n"
        "    async def find_all(self):\n"
        "        return [{'id': 1, 'name': 'Alice'}]\n"
    )
    (db / "post_repo.py").write_text(
        "class PostRepo:\n"
        "    async def find_all(self):\n"
        "        return []\n"
    )

    # Utils
    utils = tmp_path / "app" / "utils"
    utils.mkdir(parents=True)
    (utils / "__init__.py").write_text("")
    (utils / "logger.py").write_text(
        "import logging\n"
        "\n"
        "def get_logger(name):\n"
        "    return logging.getLogger(name)\n"
    )

    # App init
    (tmp_path / "app" / "__init__.py").write_text("")

    # pyproject.toml
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\nversion = "1.0.0"\n'
    )

    return tmp_path


@pytest.fixture
def circular_repo(tmp_path: Path) -> Path:
    """Create a Python repo with circular imports."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")

    (pkg / "a.py").write_text("from pkg.b import b_val\na_val = 1\n")
    (pkg / "b.py").write_text("from pkg.c import c_val\nb_val = 2\n")
    (pkg / "c.py").write_text("from pkg.a import a_val\nc_val = 3\n")
    (pkg / "d.py").write_text("from pkg.a import a_val\nd_val = 4\n")
    (pkg / "e.py").write_text("from pkg.d import d_val\ne_val = 5\n")

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\nversion = "1.0.0"\n'
    )
    return tmp_path


class TestPythonDataFlowDetector:
    """Tests for PythonDataFlowDetector."""

    def test_detects_import_graph(self, python_repo: Path):
        """Detects import graph with correct stats."""
        ctx = DetectorContext(
            repo_root=python_repo,
            selected_languages={"python"},
            max_files=100,
        )
        detector = PythonDataFlowDetector()
        result = detector.detect(ctx)

        graph_rules = [r for r in result.rules if r.id == "python.data_flow.import_graph"]
        assert len(graph_rules) == 1
        rule = graph_rules[0]
        assert rule.stats["total_files"] >= 6
        assert rule.stats["total_edges"] >= 4

    def test_detects_endpoint_chains(self, python_repo: Path):
        """Traces endpoint chains from API to stores."""
        ctx = DetectorContext(
            repo_root=python_repo,
            selected_languages={"python"},
            max_files=100,
        )
        detector = PythonDataFlowDetector()
        result = detector.detect(ctx)

        chain_rules = [r for r in result.rules if r.id == "python.data_flow.endpoint_chains"]
        assert len(chain_rules) == 1
        rule = chain_rules[0]
        assert rule.stats["chain_count"] >= 2

        chains = rule.stats["chains"]
        user_chain = [c for c in chains if "api/users.py" in c["endpoint"]]
        assert len(user_chain) >= 1
        assert len(user_chain[0]["services"]) >= 1
        assert len(user_chain[0]["stores"]) >= 1

    def test_detects_service_dependencies(self, python_repo: Path):
        """Maps service to store dependencies."""
        ctx = DetectorContext(
            repo_root=python_repo,
            selected_languages={"python"},
            max_files=100,
        )
        detector = PythonDataFlowDetector()
        result = detector.detect(ctx)

        dep_rules = [r for r in result.rules if r.id == "python.data_flow.service_dependencies"]
        assert len(dep_rules) == 1
        assert dep_rules[0].stats["dependency_count"] >= 2

    def test_detects_circular_dependencies(self, circular_repo: Path):
        """Reports circular dependencies in import graph."""
        ctx = DetectorContext(
            repo_root=circular_repo,
            selected_languages={"python"},
            max_files=100,
        )
        detector = PythonDataFlowDetector()
        result = detector.detect(ctx)

        graph_rules = [r for r in result.rules if r.id == "python.data_flow.import_graph"]
        assert len(graph_rules) == 1
        assert graph_rules[0].stats["cycle_count"] >= 1

    def test_no_rules_on_empty_repo(self, tmp_path: Path):
        """No rules emitted for empty repo."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "empty"\n')
        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"python"},
            max_files=100,
        )
        detector = PythonDataFlowDetector()
        result = detector.detect(ctx)
        assert len(result.rules) == 0
