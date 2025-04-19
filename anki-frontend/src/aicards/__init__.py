# This file is the entry point for the Anki addon.
# It imports necessary Anki modules and defines the addon functionality.

from aqt import mw  # Main Anki window
from aqt.qt import *  # Qt components
from aqt.utils import showInfo  # For showing message boxes


# Define a function that will be called when our menu item is clicked
def show_hello_world() -> None:
    showInfo("Hello World from My Anki Addon!")


# Create a new menu item in Anki's Tools menu
action = QAction("Hello World Addon", mw)
# Connect the menu item to our function
action.triggered.connect(show_hello_world)
# Add the menu item to Anki's Tools menu
mw.form.menuTools.addAction(action)
