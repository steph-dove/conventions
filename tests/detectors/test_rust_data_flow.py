"""Integration tests for Rust data flow detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext, DetectorResult
from conventions.detectors.rust.data_flow import RustDataFlowDetector


@pytest.fixture
def rust_repo(tmp_path: Path) -> Path:
    """Create a Rust repo with layered architecture."""
    # Cargo.toml
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "myapp"\nversion = "0.1.0"\nedition = "2021"\n'
    )

    # src/main.rs
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.rs").write_text(
        "mod handlers;\nmod services;\nmod db;\nmod utils;\n\n"
        "fn main() {\n"
        '    println!("Hello");\n'
        "}\n"
    )

    # Handlers (API layer)
    handlers = src / "handlers"
    handlers.mkdir()
    (handlers / "mod.rs").write_text(
        "pub mod users;\npub mod posts;\n"
    )
    (handlers / "users.rs").write_text(
        "use crate::services::user_service;\n\n"
        "pub fn get_users() -> Vec<String> {\n"
        "    user_service::get_all()\n"
        "}\n"
    )
    (handlers / "posts.rs").write_text(
        "use crate::services::post_service;\n\n"
        "pub fn get_posts() -> Vec<String> {\n"
        "    post_service::get_all()\n"
        "}\n"
    )

    # Services
    services = src / "services"
    services.mkdir()
    (services / "mod.rs").write_text(
        "pub mod user_service;\npub mod post_service;\n"
    )
    (services / "user_service.rs").write_text(
        "use crate::db::user_repo;\n"
        "use crate::utils::logger;\n\n"
        "pub fn get_all() -> Vec<String> {\n"
        '    logger::info("getting users");\n'
        "    user_repo::find_all()\n"
        "}\n"
    )
    (services / "post_service.rs").write_text(
        "use crate::db::post_repo;\n"
        "use crate::utils::logger;\n\n"
        "pub fn get_all() -> Vec<String> {\n"
        '    logger::info("getting posts");\n'
        "    post_repo::find_all()\n"
        "}\n"
    )

    # DB layer
    db = src / "db"
    db.mkdir()
    (db / "mod.rs").write_text(
        "pub mod user_repo;\npub mod post_repo;\n"
    )
    (db / "user_repo.rs").write_text(
        "pub fn find_all() -> Vec<String> {\n"
        '    vec!["Alice".to_string()]\n'
        "}\n"
    )
    (db / "post_repo.rs").write_text(
        "pub fn find_all() -> Vec<String> {\n"
        "    vec![]\n"
        "}\n"
    )

    # Utils
    utils = src / "utils"
    utils.mkdir()
    (utils / "mod.rs").write_text("pub mod logger;\n")
    (utils / "logger.rs").write_text(
        "pub fn info(msg: &str) {\n"
        '    println!("{}", msg);\n'
        "}\n"
    )

    return tmp_path


class TestRustDataFlowDetector:
    """Tests for RustDataFlowDetector."""

    def test_detects_import_graph(self, rust_repo: Path):
        """Detects import graph with correct stats."""
        ctx = DetectorContext(
            repo_root=rust_repo,
            selected_languages={"rust"},
            max_files=100,
        )
        detector = RustDataFlowDetector()
        result = detector.detect(ctx)

        graph_rules = [r for r in result.rules if r.id == "rust.data_flow.import_graph"]
        assert len(graph_rules) == 1
        rule = graph_rules[0]
        assert rule.stats["total_edges"] >= 4

    def test_detects_endpoint_chains(self, rust_repo: Path):
        """Traces endpoint chains from handlers to db."""
        ctx = DetectorContext(
            repo_root=rust_repo,
            selected_languages={"rust"},
            max_files=100,
        )
        detector = RustDataFlowDetector()
        result = detector.detect(ctx)

        chain_rules = [r for r in result.rules if r.id == "rust.data_flow.endpoint_chains"]
        assert len(chain_rules) == 1
        rule = chain_rules[0]
        assert rule.stats["chain_count"] >= 1

    def test_detects_service_dependencies(self, rust_repo: Path):
        """Maps service to db dependencies."""
        ctx = DetectorContext(
            repo_root=rust_repo,
            selected_languages={"rust"},
            max_files=100,
        )
        detector = RustDataFlowDetector()
        result = detector.detect(ctx)

        dep_rules = [r for r in result.rules if r.id == "rust.data_flow.service_dependencies"]
        assert len(dep_rules) == 1
        assert dep_rules[0].stats["dependency_count"] >= 1

    def test_no_rules_on_empty_repo(self, tmp_path: Path):
        """No rules emitted for empty repo."""
        (tmp_path / "Cargo.toml").write_text(
            '[package]\nname = "empty"\nversion = "0.1.0"\n'
        )
        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"rust"},
            max_files=100,
        )
        detector = RustDataFlowDetector()
        result = detector.detect(ctx)
        assert len(result.rules) == 0
