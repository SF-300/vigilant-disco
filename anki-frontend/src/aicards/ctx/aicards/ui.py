from abc import ABC, abstractmethod

from PyQt5.QtWidgets import QWidget

class WindowContent(ABC):
    """Abstract base class for window content."""

    @abstractmethod
    def create_content(self, window: QWidget) -> None:
        """Creates and adds content to the given window."""
        pass
