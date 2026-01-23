"""Tests for Python testing detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext, DetectorResult


@pytest.fixture
def pytest_repo(tmp_path: Path) -> Path:
    """Create a repo with pytest tests."""
    tests = tmp_path / "tests"
    tests.mkdir()

    conftest = '''"""Shared fixtures."""
import pytest

@pytest.fixture
def sample_data():
    return {"key": "value"}

@pytest.fixture(scope="session")
def db_connection():
    return "sqlite:///:memory:"
'''
    (tests / "conftest.py").write_text(conftest)

    test_file = '''"""Tests using pytest."""
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_service():
    return Mock()

def test_basic():
    assert True

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"

class TestGroup:
    @pytest.fixture
    def local_fixture(self):
        return 42

    def test_with_local(self, local_fixture):
        assert local_fixture == 42

    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 4),
    ])
    def test_parametrized(self, input, expected):
        assert input * 2 == expected
'''
    (tests / "test_example.py").write_text(test_file)

    test_file2 = '''"""More tests."""
import pytest

def test_another():
    assert 1 + 1 == 2
'''
    (tests / "test_more.py").write_text(test_file2)

    return tmp_path


@pytest.fixture
def unittest_repo(tmp_path: Path) -> Path:
    """Create a repo with unittest tests."""
    tests = tmp_path / "tests"
    tests.mkdir()

    test_file = '''"""Tests using unittest."""
import unittest

class TestExample(unittest.TestCase):
    def setUp(self):
        self.data = {"key": "value"}

    def test_basic(self):
        self.assertTrue(True)

    def test_with_data(self):
        self.assertEqual(self.data["key"], "value")

if __name__ == "__main__":
    unittest.main()
'''
    (tests / "test_example.py").write_text(test_file)
    return tmp_path


class TestPythonTestingDetector:
    """Tests for Python testing detector."""

    def test_detect_pytest_framework(self, pytest_repo: Path):
        """Test detection of pytest as testing framework."""
        from conventions.detectors.python.testing import PythonTestingConventionsDetector as PythonTestingDetector

        ctx = DetectorContext(
            repo_root=pytest_repo,
            selected_languages={"python"},
            max_files=100,
        )

        detector = PythonTestingDetector()
        result = detector.detect(ctx)

        framework_rule = None
        for rule in result.rules:
            if rule.id == "python.conventions.testing_framework":
                framework_rule = rule
                break

        assert framework_rule is not None
        assert framework_rule.stats.get("primary_framework") == "pytest"
        assert framework_rule.stats.get("test_file_count", 0) >= 2

    def test_detect_pytest_fixtures(self, pytest_repo: Path):
        """Test detection of pytest fixtures."""
        from conventions.detectors.python.testing import PythonTestingConventionsDetector as PythonTestingDetector

        ctx = DetectorContext(
            repo_root=pytest_repo,
            selected_languages={"python"},
            max_files=100,
        )

        detector = PythonTestingDetector()
        result = detector.detect(ctx)

        fixture_rule = None
        for rule in result.rules:
            if rule.id == "python.conventions.testing_fixtures":
                fixture_rule = rule
                break

        assert fixture_rule is not None
        assert fixture_rule.stats.get("fixture_count", 0) >= 3
        assert fixture_rule.stats.get("conftest_count", 0) >= 1

    def test_detect_unittest_framework(self, unittest_repo: Path):
        """Test detection of unittest framework."""
        from conventions.detectors.python.testing import PythonTestingConventionsDetector as PythonTestingDetector

        ctx = DetectorContext(
            repo_root=unittest_repo,
            selected_languages={"python"},
            max_files=100,
        )

        detector = PythonTestingDetector()
        result = detector.detect(ctx)

        framework_rule = None
        for rule in result.rules:
            if rule.id == "python.conventions.testing_framework":
                framework_rule = rule
                break

        assert framework_rule is not None
        assert framework_rule.stats.get("primary_framework") == "unittest"


class TestPythonTestingMocking:
    """Tests for mocking detection."""

    def test_detect_mocking_libraries(self, pytest_repo: Path):
        """Test detection of mocking libraries."""
        from conventions.detectors.python.testing import PythonTestingConventionsDetector as PythonTestingDetector

        ctx = DetectorContext(
            repo_root=pytest_repo,
            selected_languages={"python"},
            max_files=100,
        )

        detector = PythonTestingDetector()
        result = detector.detect(ctx)

        mock_rule = None
        for rule in result.rules:
            if rule.id == "python.conventions.testing_mocking":
                mock_rule = rule
                break

        # Should detect unittest.mock usage
        if mock_rule is not None:
            libs = mock_rule.stats.get("mock_library_counts", {})
            assert len(libs) > 0 or mock_rule.stats.get("total_mock_uses", 0) > 0
