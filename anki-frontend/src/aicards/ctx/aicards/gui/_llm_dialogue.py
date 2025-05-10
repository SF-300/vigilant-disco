from PyQt5.QtWidgets import (
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
)
from PyQt5.QtCore import Qt


class MessageBubble(QWidget):
    """A single LLM message (role + text) styled like a chat bubble."""
    def __init__(self, role: str, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        # Create a header with role name
        header = QLabel(role.upper(), self)
        header.setStyleSheet("font-size:8pt; font-weight:bold; color: #606060; margin-left:3px;")
        
        # Create the message body
        body = QLabel(text, self)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # Make text selectable
        
        # Different styling based on the role
        role_colors = {
            "system": "#e3f2fd",           # Light blue
            "ocr": "#fff8e1",              # Light amber
            "ocr-request": "#fffde7",      # Light yellow
            "ocr-response": "#f1f8e9",     # Light green
            "generation-request": "#e8f5e9", # Light green
            "generation-response": "#e0f2f1", # Light teal
            "export": "#f3e5f5",           # Light purple
            "export-complete": "#e8eaf6",  # Light indigo
        }
        
        color = role_colors.get(role.lower(), "#f5f5f5")  # Default to light grey
        border_color = "#ffca28" if role.lower().startswith("ocr") else "#78909c"
        
        body.setStyleSheet(f"""
            background-color: {color};
            border: 1px solid {border_color};
            border-radius: 6px;
            padding: 8px;
            margin: 2px;
        """)
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 8)  # Add some bottom margin between messages
        layout.setSpacing(2)  # Tighter spacing between header and body
        layout.addWidget(header)
        layout.addWidget(body)
        
        # Make the widget expand horizontally but only take vertical space it needs
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)


class LLMDialoguePanel(QScrollArea):
    """Scrollable container for multiple MessageBubble widgets."""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        # Create a container widget with a vertical layout
        outer_widget = QWidget()
        outer_layout = QVBoxLayout(outer_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add a title label at the top
        title_label = QLabel("LLM Dialogue")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-weight: bold;
            background-color: #455a64; 
            color: white;
            padding: 4px;
        """)
        outer_layout.addWidget(title_label)
        
        # Create the scroll area for messages
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(0)  # No frame
        
        # Create the container widget that will hold all message bubbles
        messages_container = QWidget()
        self._layout = QVBoxLayout(messages_container)
        self._layout.addStretch()  # Push content to the top, new messages at bottom
        
        # Set margins for better appearance
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(8)  # Space between messages
        
        # Configure the scroll area with our message container
        scroll_area.setWidget(messages_container)
        outer_layout.addWidget(scroll_area, 1)  # Give the scroll area all available space
        
        # Set minimum width for the panel
        self.setMinimumWidth(300)
        
        # Apply outer layout to self
        self.setWidget(outer_widget)
        self.setWidgetResizable(True)
        self.setFrameStyle(QLabel.Box | QLabel.Sunken)
        
        # Add a placeholder when empty
        self._placeholder = QLabel("LLM interaction will appear here")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: gray; font-style: italic;")
        self._layout.insertWidget(0, self._placeholder)

    # def add_message(self, role: str, text: str) -> None:
    #     """Add a new message bubble to the dialogue panel.
        
    #     Args:
    #         role: The role of the message sender (e.g., "system", "user", "ocr")
    #         text: The text content of the message
    #     """
    #     # Remove placeholder if it's the first message
    #     if self._placeholder.parent():
    #         self._layout.removeWidget(self._placeholder)
    #         self._placeholder.setParent(None)
        
    #     # Create the message bubble
    #     bubble = MessageBubble(role, text)
        
    #     # Insert before the stretch spacer at the bottom
    #     self._layout.insertWidget(self._layout.count() - 1, bubble)
        
    #     # Auto-scroll to show the new message
    #     self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        
    # def _clear_messages(self) -> None:
    #     """Clear all messages from the dialogue panel."""
    #     # Remove all message bubbles but keep the stretch at the end
    #     while self._layout.count() > 1:  # Keep the stretch
    #         item = self._layout.itemAt(0)
    #         if item and item.widget():
    #             widget = item.widget()
    #             self._layout.removeWidget(widget)
    #             widget.deleteLater()
        
    #     # Add the placeholder back
    #     self._placeholder.setParent(self)
    #     self._layout.insertWidget(0, self._placeholder)
