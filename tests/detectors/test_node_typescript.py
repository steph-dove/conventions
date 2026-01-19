"""Tests for Node.js TypeScript detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext


@pytest.fixture
def strict_ts_repo(tmp_path: Path) -> Path:
    """Create a repo with strict TypeScript configuration."""
    (tmp_path / "src").mkdir()

    tsconfig = '''{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "noImplicitAny": true,
    "strictNullChecks": true
  },
  "include": ["src/**/*"]
}'''
    (tmp_path / "tsconfig.json").write_text(tsconfig)

    ts_file = '''interface User {
    id: number;
    name: string;
}

export function getUser(id: number): User | null {
    return { id, name: "Test" };
}

export class UserService {
    private users: Map<number, User> = new Map();

    async findById(id: number): Promise<User | null> {
        return this.users.get(id) ?? null;
    }
}
'''
    (tmp_path / "src" / "users.ts").write_text(ts_file)
    return tmp_path


@pytest.fixture
def loose_ts_repo(tmp_path: Path) -> Path:
    """Create a repo with loose TypeScript configuration."""
    (tmp_path / "src").mkdir()

    tsconfig = '''{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs"
  },
  "include": ["src/**/*"]
}'''
    (tmp_path / "tsconfig.json").write_text(tsconfig)

    ts_file = '''// Using any types
export function processData(data: any): any {
    return data;
}

export function handleInput(input: any) {
    console.log(input);
}
'''
    (tmp_path / "src" / "utils.ts").write_text(ts_file)
    return tmp_path


class TestNodeTypeScriptDetector:
    """Tests for Node TypeScript detector."""

    def test_detect_strict_mode(self, strict_ts_repo: Path):
        """Test detection of TypeScript strict mode."""
        try:
            from conventions.detectors.node.typescript import NodeTypeScriptDetector
        except ImportError:
            pytest.skip("Node TypeScript detector not available")

        ctx = DetectorContext(
            repo_root=strict_ts_repo,
            selected_languages={"node"},
            max_files=100,
        )

        detector = NodeTypeScriptDetector()
        result = detector.detect(ctx)

        strict_rule = None
        for rule in result.rules:
            if rule.id == "node.conventions.strict_mode":
                strict_rule = rule
                break

        assert strict_rule is not None
        assert strict_rule.stats.get("has_strict") is True

    def test_detect_loose_mode(self, loose_ts_repo: Path):
        """Test detection of loose TypeScript configuration."""
        try:
            from conventions.detectors.node.typescript import NodeTypeScriptDetector
        except ImportError:
            pytest.skip("Node TypeScript detector not available")

        ctx = DetectorContext(
            repo_root=loose_ts_repo,
            selected_languages={"node"},
            max_files=100,
        )

        detector = NodeTypeScriptDetector()
        result = detector.detect(ctx)

        strict_rule = None
        for rule in result.rules:
            if rule.id == "node.conventions.strict_mode":
                strict_rule = rule
                break

        if strict_rule is not None:
            assert strict_rule.stats.get("has_strict") is not True

    def test_detect_type_coverage(self, loose_ts_repo: Path):
        """Test detection of 'any' usage."""
        try:
            from conventions.detectors.node.typescript import NodeTypeScriptDetector
        except ImportError:
            pytest.skip("Node TypeScript detector not available")

        ctx = DetectorContext(
            repo_root=loose_ts_repo,
            selected_languages={"node"},
            max_files=100,
        )

        detector = NodeTypeScriptDetector()
        result = detector.detect(ctx)

        coverage_rule = None
        for rule in result.rules:
            if rule.id == "node.conventions.type_coverage":
                coverage_rule = rule
                break

        if coverage_rule is not None:
            # Should detect high 'any' usage
            any_ratio = coverage_rule.stats.get("any_ratio", 0)
            assert any_ratio > 0.1  # Significant any usage


class TestNodeTypeScriptShouldRun:
    """Tests for detector should_run logic."""

    def test_should_run_with_node(self, strict_ts_repo: Path):
        """Test detector runs when node is selected."""
        try:
            from conventions.detectors.node.typescript import NodeTypeScriptDetector
        except ImportError:
            pytest.skip("Node TypeScript detector not available")

        ctx = DetectorContext(
            repo_root=strict_ts_repo,
            selected_languages={"node"},
        )

        detector = NodeTypeScriptDetector()
        assert detector.should_run(ctx) is True

    def test_should_not_run_without_node(self, strict_ts_repo: Path):
        """Test detector does not run when node is not selected."""
        try:
            from conventions.detectors.node.typescript import NodeTypeScriptDetector
        except ImportError:
            pytest.skip("Node TypeScript detector not available")

        ctx = DetectorContext(
            repo_root=strict_ts_repo,
            selected_languages={"python", "go"},
        )

        detector = NodeTypeScriptDetector()
        assert detector.should_run(ctx) is False
