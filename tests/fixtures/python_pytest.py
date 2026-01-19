"""Example pytest test file."""
import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {"name": "test", "values": [1, 2, 3, 4, 5]}


@pytest.fixture
def mock_service():
    """Mock service for testing."""
    service = Mock()
    service.get_user.return_value = {"id": 1, "name": "Test User"}
    return service


class TestCalculations:
    """Tests for calculation functions."""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance."""
        from .python_untyped import Calculator
        return Calculator(precision=2)

    def test_add(self, calculator):
        """Test addition."""
        assert calculator.add(1.234, 2.345) == 3.58

    def test_subtract(self, calculator):
        """Test subtraction."""
        assert calculator.subtract(5.0, 3.2) == 1.8

    @pytest.mark.parametrize("a,b,expected", [
        (2, 3, 6),
        (0, 5, 0),
        (-1, 4, -4),
    ])
    def test_multiply_parametrized(self, calculator, a, b, expected):
        """Test multiplication with various inputs."""
        assert calculator.multiply(a, b) == expected


def test_process_data_with_positive():
    """Test processing positive numbers."""
    from .python_untyped import process_data
    result = process_data([1, 2, 3])
    assert result == [2, 4, 6]


def test_process_data_with_negative():
    """Test processing with negative numbers."""
    from .python_untyped import process_data
    result = process_data([-1, 0, 1])
    assert result == [2]  # Only positive numbers are processed


def test_greet_informal(sample_data):
    """Test informal greeting."""
    from .python_typed import greet
    assert greet("World") == "Hello, World!"


def test_greet_formal():
    """Test formal greeting."""
    from .python_typed import greet
    assert greet("Sir", formal=True) == "Good day, Sir"


@patch("some_module.external_api")
def test_with_mock(mock_api):
    """Test with mocked external API."""
    mock_api.return_value = {"status": "ok"}
    # Test logic would go here
    assert mock_api.called is False  # Not called yet


@pytest.mark.asyncio
async def test_async_operation():
    """Test async function."""
    from .python_typed import UserService
    service = UserService("sqlite:///:memory:")
    result = await service.get_user_async(1)
    assert result["id"] == 1
