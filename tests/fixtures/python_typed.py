"""Example of well-typed Python code."""
from typing import Optional, List, Dict, Any


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
    """Process a list of items and return their sum.

    Args:
        items: List of integers to process

    Returns:
        Sum of items, or None if empty
    """
    if not items:
        return None
    return sum(items)


def calculate_stats(data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate statistics from data.

    Args:
        data: Input data dictionary

    Returns:
        Dictionary of calculated stats
    """
    values = data.get("values", [])
    if not values:
        return {"mean": 0.0, "total": 0.0}

    return {
        "mean": sum(values) / len(values),
        "total": float(sum(values)),
    }


class UserService:
    """Service for user operations."""

    def __init__(self, db_url: str) -> None:
        """Initialize the service.

        Args:
            db_url: Database connection URL
        """
        self.db_url = db_url

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID.

        Args:
            user_id: The user's ID

        Returns:
            User dictionary or None if not found
        """
        return {"id": user_id, "name": "Test User"}

    async def get_user_async(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID asynchronously.

        Args:
            user_id: The user's ID

        Returns:
            User dictionary or None if not found
        """
        return {"id": user_id, "name": "Test User"}
