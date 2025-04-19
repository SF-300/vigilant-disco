import sys

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt

from aicards.ctx.aicards.ui import WindowContent
from aicards.ctx.aicards.gui import HelloWorldContent

# Global app variable to ensure only one QApplication instance
app = None

def show_generic_window(content: WindowContent):
    """Shows a window with the given content."""
    window = QWidget()
    window.setWindowTitle("Generic Window")
    content.create_content(window)
    window.setAttribute(
        Qt.WA_DeleteOnClose
    )  # Ensure window is deleted when closed
    window.show()

def show_menu():
    """Shows a simple window with 'Hello World'."""
    show_generic_window(HelloWorldContent())


def main():
    global app
    # Create a standalone PyQt application
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    # Call the main window function from the add-on
    show_menu()

    # Execute the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()