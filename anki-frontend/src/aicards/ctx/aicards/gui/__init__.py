import asyncio
import contextlib
import typing as t

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QTreeWidget,
    QSizePolicy,
)

from aicards.ctx.aicards.base import (
    IService,
    Extraction,
    Image,
    ExtractionWithPrototonotes,
)
from aicards.ctx.aicards.gui._extraction import (
    clipboard_pastes_processor,
    image_file_dialog_processor,
    extractions_processor,
)
from aicards.ctx.aicards.gui._protonotes import protonotes_creating_processor
from aicards.ctx.aicards.gui._export import exports_processor
from aicards.ctx.aicards.gui._llm_dialogue import LLMDialoguePanel


class AICardsContainer(QWidget):
    @classmethod
    @contextlib.asynccontextmanager
    async def running(
        cls,
        service: IService,
        parent: QWidget | None,
    ) -> t.AsyncIterator[t.Self]:
        async with asyncio.TaskGroup() as tg:
            self = cls(service, parent, tg)
            yield self

    def __init__(
        self,
        service: IService,
        parent: QWidget | None,
        tg: asyncio.TaskGroup,
    ) -> None:
        super().__init__(parent)
        self.service = service

        # Create the main horizontal layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Create left panel with vertical layout for the main workflow
        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)

        # Create workflow widgets and get the needed references directly
        (
            workflow_container,
            self._image_area,
            self._extractions_list,
            self._confirm_extractions,
        ) = create_top_section(left_panel)
        self._notes_tree = create_notes_preview(left_panel)
        self._confirm_protonotes = create_export_button(left_panel)
        self._llm_dialogue = LLMDialoguePanel(self)

        # Add widgets to left panel
        left_layout.addWidget(workflow_container)
        left_layout.addWidget(self._notes_tree)
        left_layout.addWidget(self._confirm_protonotes)

        # Add the panels to main layout
        main_layout.addWidget(left_panel, stretch=2)
        main_layout.addWidget(self._llm_dialogue, stretch=1)

        _extractions_q = asyncio.Queue[Image]()
        _protonotes_q = asyncio.Queue[t.Sequence[Extraction]]()
        _exports_q = asyncio.Queue[t.Sequence[ExtractionWithPrototonotes]]()

        tg.create_task(
            clipboard_pastes_processor(
                _extractions_q,
                self._image_area,
                self._llm_dialogue.add_message,
            )
        )

        tg.create_task(
            image_file_dialog_processor(
                _extractions_q,
                self._image_area,
                self._llm_dialogue.add_message,
            )
        )

        tg.create_task(
            extractions_processor(
                _extractions_q,
                _protonotes_q,
                self._extractions_list,
                self._confirm_extractions,
                service,
                self._llm_dialogue.add_message,
            )
        )
        tg.create_task(
            protonotes_creating_processor(
                _protonotes_q,
                _exports_q,
                self._notes_tree,
                self._confirm_protonotes,
                service,
                self._llm_dialogue.add_message,
            )
        )
        tg.create_task(
            exports_processor(
                _exports_q,
                service,
                self._llm_dialogue.add_message,
            )
        )

    @property
    def image_area(self) -> QPushButton:
        return self._image_area

    @property
    def extractions_list(self) -> QListWidget:
        return self._extractions_list

    @property
    def confirm_extractions_button(self) -> QPushButton:
        return self._confirm_extractions

    @property
    def notes_tree(self) -> QTreeWidget:
        return self._notes_tree

    @property
    def confirm_protonotes_button(self) -> QPushButton:
        return self._confirm_protonotes


def create_main_layout(*widgets: QWidget) -> QVBoxLayout:
    layout = QVBoxLayout()
    for widget in widgets:
        layout.addWidget(widget)
    return layout


def create_top_section(
    parent: QWidget,
) -> tuple[QWidget, QPushButton, QListWidget, QPushButton]:
    container = QWidget(parent)
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)  # Remove outer margins
    layout.setSpacing(10)  # Add spacing between image area and the extractions list

    # Create the image area on the left
    image_area = create_image_area(container)
    layout.addWidget(image_area)

    # Create a vertical layout for the extractions list and the confirm button
    right_column = QWidget(container)
    right_column.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Preferred,
    )
    right_layout = QVBoxLayout(right_column)
    right_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
    right_layout.setSpacing(5)  # Small spacing between list and button

    # Add extractions list
    extractions_list = create_extractions_list(right_column)
    right_layout.addWidget(extractions_list)

    # Add confirm button right below the extractions list
    confirm_button = create_confirm_button(right_column)
    right_layout.addWidget(confirm_button)  # No alignment to allow natural expansion

    # Add the right column to the main layout
    layout.addWidget(right_column)

    container.setLayout(layout)
    return container, image_area, extractions_list, confirm_button


def create_image_area(parent: QWidget) -> QPushButton:
    button = QPushButton("Click here to select an image or paste with Ctrl+V", parent)
    button.setMinimumSize(400, 300)
    button.setFlat(True)  # Make it look more like a label
    button.setCursor(Qt.CursorShape.PointingHandCursor)  # Show it's clickable
    button.setStyleSheet("""
        QPushButton {
            text-align: center;
            border: 1px solid #aaa;
            background-color: #f8f8f8;
        }
        QPushButton:hover {
            background-color: #f0f0f0;
        }
    """)
    return button


def create_extractions_list(parent: QWidget) -> QListWidget:
    widget = QListWidget(parent)
    widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    return widget


def create_confirm_button(parent: QWidget) -> QPushButton:
    button = QPushButton("↓ Process Selected Extractions ↓", parent)
    # Don't set a maximum width, so it can expand to the width of its container
    button.setSizePolicy(
        QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
    )
    return button


def create_notes_preview(parent: QWidget) -> QTreeWidget:
    tree = QTreeWidget(parent)
    tree.setHeaderLabels(["Type", "Description"])
    tree.setMinimumHeight(200)
    return tree


def create_export_button(parent: QWidget) -> QPushButton:
    return QPushButton("Import into Anki database", parent)
