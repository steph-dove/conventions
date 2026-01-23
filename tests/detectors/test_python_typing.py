"""Tests for Python typing detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext, DetectorResult


@pytest.fixture
def typed_repo(tmp_path: Path) -> Path:
    """Create a repo with well-typed Python code."""
    src = tmp_path / "src"
    src.mkdir()

    typed_code = '''"""Well-typed module."""
from typing import Optional, List, Dict

def greet(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"

def add_numbers(a: int, b: int) -> int:
    return a + b

def process_items(items: List[int]) -> Optional[int]:
    if not items:
        return None
    return sum(items)

class UserService:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def get_user(self, user_id: int) -> Dict[str, str]:
        return {"id": str(user_id)}
'''
    (src / "typed.py").write_text(typed_code)
    return tmp_path


@pytest.fixture
def untyped_repo(tmp_path: Path) -> Path:
    """Create a repo with untyped Python code."""
    src = tmp_path / "src"
    src.mkdir()

    untyped_code = '''"""Untyped module."""

def greet(name):
    return f"Hello, {name}!"

def add_numbers(a, b):
    return a + b

def process_items(items):
    if not items:
        return None
    return sum(items)

class UserService:
    def __init__(self, db_url):
        self.db_url = db_url

    def get_user(self, user_id):
        return {"id": str(user_id)}
'''
    (src / "untyped.py").write_text(untyped_code)
    return tmp_path


@pytest.fixture
def mixed_repo(tmp_path: Path) -> Path:
    """Create a repo with mixed typing."""
    src = tmp_path / "src"
    src.mkdir()

    typed_code = '''"""Typed module."""
def typed_func(x: int) -> int:
    return x * 2
'''
    (src / "typed.py").write_text(typed_code)

    untyped_code = '''"""Untyped module."""
def untyped_func(x):
    return x * 2
'''
    (src / "untyped.py").write_text(untyped_code)
    return tmp_path


class TestPythonTypingDetector:
    """Tests for Python typing coverage detection."""

    def test_detect_high_typing_coverage(self, typed_repo: Path):
        """Test detection of high typing coverage."""
        from conventions.detectors.python.typing import PythonTypingConventionsDetector as PythonTypingDetector

        ctx = DetectorContext(
            repo_root=typed_repo,
            selected_languages={"python"},
            max_files=100,
        )

        detector = PythonTypingDetector()
        result = detector.detect(ctx)

        assert isinstance(result, DetectorResult)
        assert len(result.rules) > 0

        typing_rule = None
        for rule in result.rules:
            if rule.id == "python.conventions.typing_coverage":
                typing_rule = rule
                break

        assert typing_rule is not None
        assert typing_rule.confidence > 0.5
        coverage = typing_rule.stats.get("any_annotation_coverage", 0)
        assert coverage > 0.5  # High coverage expected

    def test_detect_low_typing_coverage(self, untyped_repo: Path):
        """Test detection of low typing coverage."""
        from conventions.detectors.python.typing import PythonTypingConventionsDetector as PythonTypingDetector

        ctx = DetectorContext(
            repo_root=untyped_repo,
            selected_languages={"python"},
            max_files=100,
        )

        detector = PythonTypingDetector()
        result = detector.detect(ctx)

        typing_rule = None
        for rule in result.rules:
            if rule.id == "python.conventions.typing_coverage":
                typing_rule = rule
                break

        assert typing_rule is not None
        coverage = typing_rule.stats.get("any_annotation_coverage", 0)
        assert coverage < 0.5  # Low coverage expected

    def test_detect_mixed_typing(self, mixed_repo: Path):
        """Test detection of mixed typing coverage."""
        from conventions.detectors.python.typing import PythonTypingConventionsDetector as PythonTypingDetector

        ctx = DetectorContext(
            repo_root=mixed_repo,
            selected_languages={"python"},
            max_files=100,
        )

        detector = PythonTypingDetector()
        result = detector.detect(ctx)

        typing_rule = None
        for rule in result.rules:
            if rule.id == "python.conventions.typing_coverage":
                typing_rule = rule
                break

        assert typing_rule is not None
        # Mixed repo should have moderate coverage
        coverage = typing_rule.stats.get("any_annotation_coverage", 0)
        assert 0.3 <= coverage <= 0.7


class TestPythonTypingDetectorShouldRun:
    """Tests for detector should_run logic."""

    def test_should_run_with_python(self, typed_repo: Path):
        """Test detector runs when Python is selected."""
        from conventions.detectors.python.typing import PythonTypingConventionsDetector as PythonTypingDetector

        ctx = DetectorContext(
            repo_root=typed_repo,
            selected_languages={"python"},
        )

        detector = PythonTypingDetector()
        assert detector.should_run(ctx) is True

    def test_should_not_run_without_python(self, typed_repo: Path):
        """Test detector does not run when Python is not selected."""
        from conventions.detectors.python.typing import PythonTypingConventionsDetector as PythonTypingDetector

        ctx = DetectorContext(
            repo_root=typed_repo,
            selected_languages={"go", "node"},
        )

        detector = PythonTypingDetector()
        assert detector.should_run(ctx) is False
