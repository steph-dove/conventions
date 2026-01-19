"""Shared pytest fixtures for conventions tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from conventions.config import ConventionsConfig
from conventions.detectors.base import DetectorContext
from conventions.schemas import ConventionRule, ConventionsOutput, EvidenceSnippet, RepoMetadata


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create a minimal repository structure for testing."""
    # Create basic structure
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".git").mkdir()

    # Create a .gitignore
    (tmp_path / ".gitignore").write_text("*.pyc\n__pycache__/\n.venv/\n")

    return tmp_path


@pytest.fixture
def sample_repo(tmp_repo: Path) -> Path:
    """Create a sample repository with Python files for testing."""
    # Create Python files
    typed_py = '''"""Typed module example."""
from typing import Optional, List

def greet(name: str, formal: bool = False) -> str:
    """Greet someone by name.

    Args:
        name: The person's name
        formal: Whether to use formal greeting

    Returns:
        A greeting string
    """
    if formal:
        return f"Good day, {name}"
    return f"Hello, {name}!"

def process_items(items: List[int]) -> Optional[int]:
    """Process a list of items."""
    if not items:
        return None
    return sum(items)

class UserService:
    """Service for user operations."""

    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def get_user(self, user_id: int) -> dict:
        """Get user by ID."""
        return {"id": user_id, "name": "Test User"}
'''
    (tmp_repo / "src" / "typed_module.py").write_text(typed_py)

    untyped_py = '''"""Untyped module example."""

def add(a, b):
    return a + b

def multiply(x, y):
    result = x * y
    return result

class Calculator:
    def __init__(self, precision):
        self.precision = precision

    def divide(self, a, b):
        return round(a / b, self.precision)
'''
    (tmp_repo / "src" / "untyped_module.py").write_text(untyped_py)

    test_py = '''"""Test module example."""
import pytest

from src.typed_module import greet, process_items

@pytest.fixture
def sample_items():
    """Sample items for testing."""
    return [1, 2, 3, 4, 5]

def test_greet():
    assert greet("World") == "Hello, World!"
    assert greet("World", formal=True) == "Good day, World"

def test_process_items(sample_items):
    assert process_items(sample_items) == 15

def test_process_empty():
    assert process_items([]) is None

class TestUserService:
    """Tests for UserService."""

    @pytest.fixture
    def service(self):
        return UserService("sqlite:///:memory:")

    def test_get_user(self, service):
        user = service.get_user(1)
        assert user["id"] == 1
'''
    (tmp_repo / "tests" / "test_typed.py").write_text(test_py)

    # Create conftest.py
    conftest = '''"""Shared test fixtures."""
import pytest

@pytest.fixture(scope="session")
def db_url():
    """Database URL for testing."""
    return "sqlite:///:memory:"
'''
    (tmp_repo / "tests" / "conftest.py").write_text(conftest)

    return tmp_repo


@pytest.fixture
def node_sample_repo(tmp_repo: Path) -> Path:
    """Create a sample repository with TypeScript files for testing."""
    (tmp_repo / "src").mkdir(exist_ok=True)

    ts_file = '''import { User } from './types';

interface Config {
    apiUrl: string;
    timeout: number;
}

/**
 * Fetch user by ID
 * @param id - User ID
 * @returns User object or null
 */
export async function getUser(id: number): Promise<User | null> {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) {
        return null;
    }
    return response.json();
}

export class UserService {
    private config: Config;

    constructor(config: Config) {
        this.config = config;
    }

    async findById(id: number): Promise<User | null> {
        return getUser(id);
    }
}
'''
    (tmp_repo / "src" / "users.ts").write_text(ts_file)

    tsconfig = '''{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist"
  },
  "include": ["src/**/*"]
}
'''
    (tmp_repo / "tsconfig.json").write_text(tsconfig)

    package_json = '''{
  "name": "sample-project",
  "version": "1.0.0",
  "scripts": {
    "test": "jest",
    "build": "tsc"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "jest": "^29.0.0"
  }
}
'''
    (tmp_repo / "package.json").write_text(package_json)

    return tmp_repo


@pytest.fixture
def detector_context(sample_repo: Path) -> DetectorContext:
    """Create a DetectorContext for testing detectors."""
    return DetectorContext(
        repo_root=sample_repo,
        selected_languages={"python"},
        max_files=100,
        max_evidence_snippets=5,
    )


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Create a test .conventionsrc.json file."""
    config_data = {
        "languages": ["python"],
        "max_files": 500,
        "disabled_detectors": ["python_graphql"],
        "disabled_rules": ["python.conventions.graphql"],
        "output_formats": ["json", "markdown"],
        "exclude_patterns": ["**/generated/**", "**/vendor/**"],
        "min_score": 3.0
    }
    config_path = tmp_path / ".conventionsrc.json"
    config_path.write_text(json.dumps(config_data, indent=2))
    return config_path


@pytest.fixture
def sample_rule() -> ConventionRule:
    """Create a sample ConventionRule for testing."""
    return ConventionRule(
        id="python.conventions.testing_framework",
        category="testing",
        title="Testing Framework",
        description="Uses pytest as the primary testing framework",
        confidence=0.95,
        language="python",
        evidence=[
            EvidenceSnippet(
                file_path="tests/test_example.py",
                line_start=1,
                line_end=10,
                excerpt="import pytest\n\ndef test_example():\n    assert True",
            )
        ],
        stats={
            "primary_framework": "pytest",
            "test_file_count": 5,
        }
    )


@pytest.fixture
def sample_output(sample_rule: ConventionRule) -> ConventionsOutput:
    """Create a sample ConventionsOutput for testing."""
    return ConventionsOutput(
        version="1.0.0",
        metadata=RepoMetadata(
            path="/test/repo",
            detected_languages=["python"],
            total_files_scanned=20,
        ),
        rules=[sample_rule],
        warnings=[],
    )


@pytest.fixture
def default_config() -> ConventionsConfig:
    """Create a default ConventionsConfig for testing."""
    return ConventionsConfig()


@pytest.fixture
def custom_config() -> ConventionsConfig:
    """Create a customized ConventionsConfig for testing."""
    return ConventionsConfig(
        languages=["python", "go"],
        max_files=1000,
        disabled_detectors=["python_graphql"],
        disabled_rules=["python.conventions.graphql"],
        output_formats=["json", "markdown", "html"],
        exclude_patterns=["**/generated/**"],
        plugin_paths=["./custom_rules.py"],
        min_score=3.5,
    )
