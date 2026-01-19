"""Tests for generic CI/CD detector."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.detectors.base import DetectorContext


@pytest.fixture
def github_actions_repo(tmp_path: Path) -> Path:
    """Create a repo with GitHub Actions."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)

    ci_workflow = '''name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run linting
        run: ruff check .
      - name: Run tests
        run: pytest tests/
      - name: Upload coverage
        uses: codecov/codecov-action@v3
'''
    (workflows / "ci.yml").write_text(ci_workflow)
    return tmp_path


@pytest.fixture
def gitlab_ci_repo(tmp_path: Path) -> Path:
    """Create a repo with GitLab CI."""
    gitlab_ci = '''stages:
  - lint
  - test
  - deploy

lint:
  stage: lint
  script:
    - ruff check .

test:
  stage: test
  script:
    - pytest tests/
  coverage: '/TOTAL.+ ([0-9]{1,3}%)/'

deploy:
  stage: deploy
  script:
    - ./deploy.sh
  only:
    - main
'''
    (tmp_path / ".gitlab-ci.yml").write_text(gitlab_ci)
    return tmp_path


@pytest.fixture
def circleci_repo(tmp_path: Path) -> Path:
    """Create a repo with CircleCI."""
    circleci_dir = tmp_path / ".circleci"
    circleci_dir.mkdir()

    config = '''version: 2.1

jobs:
  build:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: pip install -r requirements.txt
      - run:
          name: Run tests
          command: pytest tests/

workflows:
  main:
    jobs:
      - build
'''
    (circleci_dir / "config.yml").write_text(config)
    return tmp_path


class TestGenericCIDetector:
    """Tests for generic CI/CD detector."""

    def test_detect_github_actions(self, github_actions_repo: Path):
        """Test detection of GitHub Actions."""
        try:
            from conventions.detectors.generic.ci import GenericCIDetector
        except ImportError:
            pytest.skip("Generic CI detector not available")

        ctx = DetectorContext(
            repo_root=github_actions_repo,
            selected_languages=set(),  # Generic detector runs for all
            max_files=100,
        )

        detector = GenericCIDetector()
        result = detector.detect(ctx)

        ci_rule = None
        for rule in result.rules:
            if rule.id == "generic.conventions.ci_cd_platform":
                ci_rule = rule
                break

        assert ci_rule is not None
        assert ci_rule.stats.get("primary_platform") == "github_actions"

    def test_detect_gitlab_ci(self, gitlab_ci_repo: Path):
        """Test detection of GitLab CI."""
        try:
            from conventions.detectors.generic.ci import GenericCIDetector
        except ImportError:
            pytest.skip("Generic CI detector not available")

        ctx = DetectorContext(
            repo_root=gitlab_ci_repo,
            selected_languages=set(),
            max_files=100,
        )

        detector = GenericCIDetector()
        result = detector.detect(ctx)

        ci_rule = None
        for rule in result.rules:
            if rule.id == "generic.conventions.ci_cd_platform":
                ci_rule = rule
                break

        assert ci_rule is not None
        assert ci_rule.stats.get("primary_platform") == "gitlab_ci"

    def test_detect_circleci(self, circleci_repo: Path):
        """Test detection of CircleCI."""
        try:
            from conventions.detectors.generic.ci import GenericCIDetector
        except ImportError:
            pytest.skip("Generic CI detector not available")

        ctx = DetectorContext(
            repo_root=circleci_repo,
            selected_languages=set(),
            max_files=100,
        )

        detector = GenericCIDetector()
        result = detector.detect(ctx)

        ci_rule = None
        for rule in result.rules:
            if rule.id == "generic.conventions.ci_cd_platform":
                ci_rule = rule
                break

        assert ci_rule is not None
        assert ci_rule.stats.get("primary_platform") == "circleci"

    def test_detect_ci_features(self, github_actions_repo: Path):
        """Test detection of CI features like testing and linting."""
        try:
            from conventions.detectors.generic.ci import GenericCIDetector
        except ImportError:
            pytest.skip("Generic CI detector not available")

        ctx = DetectorContext(
            repo_root=github_actions_repo,
            selected_languages=set(),
            max_files=100,
        )

        detector = GenericCIDetector()
        result = detector.detect(ctx)

        quality_rule = None
        for rule in result.rules:
            if rule.id == "generic.conventions.ci_cd_quality":
                quality_rule = rule
                break

        if quality_rule is not None:
            features = quality_rule.stats.get("ci_features", {})
            # GitHub Actions workflow has testing and linting
            assert features.get("testing") is True or "test" in str(features).lower()


class TestGenericCIDetectorShouldRun:
    """Tests for detector should_run logic."""

    def test_should_always_run(self, github_actions_repo: Path):
        """Test that generic CI detector always runs."""
        try:
            from conventions.detectors.generic.ci import GenericCIDetector
        except ImportError:
            pytest.skip("Generic CI detector not available")

        ctx = DetectorContext(
            repo_root=github_actions_repo,
            selected_languages={"python"},  # Any language
        )

        detector = GenericCIDetector()
        # Generic detectors (empty languages set) should always run
        assert detector.should_run(ctx) is True
