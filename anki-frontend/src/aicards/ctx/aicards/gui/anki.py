# This file is the entry point for the Anki addon.
# It imports necessary Anki modules and defines the addon functionality.

from abc import ABC, abstractmethod

from aqt import mw  # Main Anki window
from aqt.qt import *  # Qt components

from aicards.ctx.aicards.ui import WindowContent
from aicards.ctx.aicards.gui import HelloWorldContent

def show_generic_window(content: WindowContent):
    """Shows a window with the given content."""
    window = QWidget()
    window.setWindowTitle("Generic Window")
    content.create_content(window)
    window.show()

def show_menu():
    """Shows a simple window with 'Hello World'."""
    show_generic_window(HelloWorldContent())

def show_anki_menu():
    # Create a new menu item in Anki's Tools menu
    action = QAction("Vigilant Addon", mw)
    # Connect the menu item to our function
    action.triggered.connect(show_menu)
    # Add the menu item to Anki's Tools menu
    mw.form.menuTools.addAction(action)
