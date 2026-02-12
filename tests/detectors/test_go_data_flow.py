"""Integration tests for Go data flow detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext, DetectorResult
from conventions.detectors.go.data_flow import GoDataFlowDetector


@pytest.fixture
def go_repo(tmp_path: Path) -> Path:
    """Create a Go repo with layered architecture."""
    # go.mod
    (tmp_path / "go.mod").write_text(
        "module github.com/example/myapp\n\ngo 1.21\n"
    )

    # API handlers
    handlers = tmp_path / "internal" / "handlers"
    handlers.mkdir(parents=True)
    (handlers / "users.go").write_text(
        'package handlers\n\n'
        'import (\n'
        '\t"github.com/example/myapp/internal/services"\n'
        '\t"github.com/example/myapp/pkg/logger"\n'
        '\t"net/http"\n'
        ')\n\n'
        'func GetUsers(w http.ResponseWriter, r *http.Request) {\n'
        '\tlogger.Info("get users")\n'
        '\tsvc := services.NewUserService()\n'
        '\tusers := svc.GetAll()\n'
        '\t_ = users\n'
        '}\n'
    )
    (handlers / "posts.go").write_text(
        'package handlers\n\n'
        'import (\n'
        '\t"github.com/example/myapp/internal/services"\n'
        '\t"net/http"\n'
        ')\n\n'
        'func GetPosts(w http.ResponseWriter, r *http.Request) {\n'
        '\tsvc := services.NewPostService()\n'
        '\tposts := svc.GetAll()\n'
        '\t_ = posts\n'
        '}\n'
    )

    # Services
    services = tmp_path / "internal" / "services"
    services.mkdir(parents=True)
    (services / "user.go").write_text(
        'package services\n\n'
        'import (\n'
        '\t"github.com/example/myapp/internal/repository"\n'
        '\t"github.com/example/myapp/pkg/logger"\n'
        ')\n\n'
        'type UserService struct {\n'
        '\trepo *repository.UserRepo\n'
        '}\n\n'
        'func NewUserService() *UserService {\n'
        '\tlogger.Info("creating user service")\n'
        '\treturn &UserService{repo: repository.NewUserRepo()}\n'
        '}\n\n'
        'func (s *UserService) GetAll() []string {\n'
        '\treturn s.repo.FindAll()\n'
        '}\n'
    )
    (services / "post.go").write_text(
        'package services\n\n'
        'import (\n'
        '\t"github.com/example/myapp/internal/repository"\n'
        '\t"github.com/example/myapp/pkg/logger"\n'
        ')\n\n'
        'type PostService struct {\n'
        '\trepo *repository.PostRepo\n'
        '}\n\n'
        'func NewPostService() *PostService {\n'
        '\tlogger.Info("creating post service")\n'
        '\treturn &PostService{repo: repository.NewPostRepo()}\n'
        '}\n\n'
        'func (s *PostService) GetAll() []string {\n'
        '\treturn s.repo.FindAll()\n'
        '}\n'
    )

    # Repository
    repo = tmp_path / "internal" / "repository"
    repo.mkdir(parents=True)
    (repo / "user.go").write_text(
        'package repository\n\n'
        'type UserRepo struct{}\n\n'
        'func NewUserRepo() *UserRepo { return &UserRepo{} }\n'
        'func (r *UserRepo) FindAll() []string { return []string{"Alice"} }\n'
    )
    (repo / "post.go").write_text(
        'package repository\n\n'
        'type PostRepo struct{}\n\n'
        'func NewPostRepo() *PostRepo { return &PostRepo{} }\n'
        'func (r *PostRepo) FindAll() []string { return nil }\n'
    )

    # Logger package
    logger = tmp_path / "pkg" / "logger"
    logger.mkdir(parents=True)
    (logger / "logger.go").write_text(
        'package logger\n\n'
        'import "fmt"\n\n'
        'func Info(msg string) { fmt.Println(msg) }\n'
    )

    # cmd/main.go
    cmd = tmp_path / "cmd"
    cmd.mkdir(parents=True)
    (cmd / "main.go").write_text(
        'package main\n\n'
        'import (\n'
        '\t"github.com/example/myapp/internal/handlers"\n'
        '\t"net/http"\n'
        ')\n\n'
        'func main() {\n'
        '\thttp.HandleFunc("/users", handlers.GetUsers)\n'
        '\thttp.ListenAndServe(":8080", nil)\n'
        '}\n'
    )

    return tmp_path


class TestGoDataFlowDetector:
    """Tests for GoDataFlowDetector."""

    def test_detects_import_graph(self, go_repo: Path):
        """Detects import graph with correct stats."""
        ctx = DetectorContext(
            repo_root=go_repo,
            selected_languages={"go"},
            max_files=100,
        )
        detector = GoDataFlowDetector()
        result = detector.detect(ctx)

        graph_rules = [r for r in result.rules if r.id == "go.data_flow.import_graph"]
        assert len(graph_rules) == 1
        rule = graph_rules[0]
        assert rule.stats["total_edges"] >= 4

    def test_detects_endpoint_chains(self, go_repo: Path):
        """Traces endpoint chains from handlers to repos."""
        ctx = DetectorContext(
            repo_root=go_repo,
            selected_languages={"go"},
            max_files=100,
        )
        detector = GoDataFlowDetector()
        result = detector.detect(ctx)

        chain_rules = [r for r in result.rules if r.id == "go.data_flow.endpoint_chains"]
        assert len(chain_rules) == 1
        rule = chain_rules[0]
        assert rule.stats["chain_count"] >= 1

    def test_detects_service_dependencies(self, go_repo: Path):
        """Maps service to store dependencies."""
        ctx = DetectorContext(
            repo_root=go_repo,
            selected_languages={"go"},
            max_files=100,
        )
        detector = GoDataFlowDetector()
        result = detector.detect(ctx)

        dep_rules = [r for r in result.rules if r.id == "go.data_flow.service_dependencies"]
        assert len(dep_rules) == 1
        assert dep_rules[0].stats["dependency_count"] >= 1

    def test_no_rules_on_empty_repo(self, tmp_path: Path):
        """No rules emitted for empty repo."""
        (tmp_path / "go.mod").write_text("module example.com/empty\n\ngo 1.21\n")
        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages={"go"},
            max_files=100,
        )
        detector = GoDataFlowDetector()
        result = detector.detect(ctx)
        assert len(result.rules) == 0
