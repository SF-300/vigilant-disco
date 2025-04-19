# Define a function that will be called when our menu item is clicked
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QAction
from aicards.ctx.aicards.ui import WindowContent

class HelloWorldContent(WindowContent):
    """Simple 'Hello World' content."""

    def create_content(self, window: QWidget) -> None:
        """Creates 'Hello World' label and adds it to the window."""
        layout = QVBoxLayout()
        label = QLabel("Hello World")
        layout.addWidget(label)
        window.setLayout(layout)

