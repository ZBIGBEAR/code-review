"""Base reviewer class."""
from abc import ABC, abstractmethod


class BaseReviewer(ABC):
    """Base class for all reviewers."""

    name: str = ""

    @abstractmethod
    def get_rules(self) -> str:
        """Return review rules for this reviewer."""
        pass
