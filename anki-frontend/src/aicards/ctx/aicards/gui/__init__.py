import asyncio
import contextlib
import typing as t
from functools import cached_property

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
    QApplication,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QBuffer, QIODevice, QByteArray
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtGui import QPainter, QLinearGradient, QColor

from aicards.ctx.aicards.base import (
    Service,
    Extraction,
    Image,
    Protonote,
    ExtractionProtonotes,
)


async def paste_receiver(
    extraction_input_queue: asyncio.Queue[Image],
    container: "AICardsContainer",
) -> None:
    clipboard = QApplication.clipboard()
    assert clipboard is not None
    paste_event_queue = asyncio.Queue[QImage]()

    def create_synthetic_image() -> QImage:
        width, height = 800, 600
        image = QImage(width, height, QImage.Format.Format_RGB32)

        painter = QPainter(image)
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0.0, QColor(255, 200, 200))
        gradient.setColorAt(1.0, QColor(200, 200, 255))

        painter.fillRect(0, 0, width, height, gradient)
        painter.end()

        return image

    # TODO: Cleanups
    def handle_clipboard_change() -> None:
        # mime_data = clipboard.mimeData()
        # if mime_data is None or not mime_data.hasImage():
        #     return

        # qt_image = clipboard.image()
        # if qt_image.isNull():
        #     return
        qt_image = create_synthetic_image()

        try:
            # Use put_nowait as this is called from the Qt event loop
            paste_event_queue.put_nowait(qt_image)
            print("Clipboard monitor: Queued image")
        except asyncio.QueueFull:
            QMessageBox.warning(container, "Error", "Processing queue is full")
        except Exception as e:
            print(f"Error handling clipboard change: {e}")

    conn = clipboard.dataChanged.connect(handle_clipboard_change)

    while True:
        print("Paste receiver: waiting for image...")
        qt_image: QImage = await paste_event_queue.get()
        print("Paste receiver: got image!")

        # Scale and display image
        scaled = qt_image.scaled(
            container.image_area.width(),
            container.image_area.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )
        pixmap = QPixmap.fromImage(scaled)
        print(f"Paste receiver: setting pixmap {pixmap.width()}x{pixmap.height()}")
        container.image_area.setPixmap(pixmap)

        # Convert to domain Image
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        qt_image.save(buffer, "PNG")
        buffer.close()

        image = Image(
            name="clipboard_image.png", mime="image/png", data=bytes(byte_array.data())
        )

        print("Paste receiver: forwarding to extraction handler")
        await extraction_input_queue.put(image)
        paste_event_queue.task_done()


async def extraction_handler(
    extraction_input_queue: asyncio.Queue[Image],
    protonote_input_queue: asyncio.Queue[t.Sequence[Extraction]],
    container: "AICardsContainer",
    service: Service,
) -> None:
    while True:
        image: Image = await extraction_input_queue.get()
        extractions = service.process_image(image)

        # Update UI
        container.extractions_list.clear()
        for extraction in extractions:
            container.extractions_list.addItem(extraction.snippet)

        await protonote_input_queue.put(extractions)
        extraction_input_queue.task_done()


async def protonote_handler(
    protonote_input_queue: asyncio.Queue[t.Sequence[Extraction]],
    export_input_queue: asyncio.Queue[
        tuple[dict[str, Protonote], t.Sequence[ExtractionProtonotes]]
    ],
    container: "AICardsContainer",
    service: Service,
) -> None:
    while True:
        extractions = await protonote_input_queue.get()

        # Wait for confirm button click
        await qt_signal_to_future(container.confirm_button.clicked)

        selected_indices = container.extractions_list.selectedIndexes()
        selected_extractions = [extractions[idx.row()] for idx in selected_indices]

        if not selected_extractions:
            protonote_input_queue.task_done()
            QMessageBox.warning(container, "Warning", "No extractions selected")
            continue

        extraction_protonotes = service.create_protonotes(selected_extractions)

        # Store protonotes with their IDs for later lookup
        id_to_protonote: dict[str, Protonote] = {}

        # Update tree
        container.notes_tree.clear()
        for ep in extraction_protonotes:
            extraction_item = QTreeWidgetItem(container.notes_tree)
            extraction_item.setText(0, ep.extraction.snippet)
            extraction_item.setFlags(
                extraction_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
            )
            extraction_item.setCheckState(0, Qt.CheckState.Checked)

            for protonote in ep.protonotes:
                note_item = QTreeWidgetItem(extraction_item)
                note_item.setText(0, protonote.description)
                note_item.setFlags(note_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                note_item.setCheckState(0, Qt.CheckState.Checked)
                # Store ID in item data for later lookup
                note_item.setData(0, Qt.ItemDataRole.UserRole, protonote.id)
                id_to_protonote[protonote.id] = protonote

        container.notes_tree.expandAll()

        await export_input_queue.put((id_to_protonote, extraction_protonotes))
        protonote_input_queue.task_done()


async def export_handler(
    export_input_queue: asyncio.Queue[
        tuple[dict[str, Protonote], t.Sequence[ExtractionProtonotes]]
    ],
    container: "AICardsContainer",
    service: Service,
) -> None:
    while True:
        id_to_protonote, _ = await export_input_queue.get()

        # Wait for export button click
        await qt_signal_to_future(container.export_button.clicked)

        # Get selected protonotes from tree
        selected_protonotes: list[Protonote] = []
        root = container.notes_tree.invisibleRootItem()
        if not root:
            export_input_queue.task_done()
            continue

        for i in range(root.childCount()):
            extraction_item = root.child(i)
            if not extraction_item:
                continue

            if extraction_item.checkState(0) == Qt.CheckState.Checked:
                for j in range(extraction_item.childCount()):
                    note_item = extraction_item.child(j)
                    if not note_item:
                        continue

                    if note_item.checkState(0) == Qt.CheckState.Checked:
                        protonote_id = note_item.data(0, Qt.ItemDataRole.UserRole)
                        if protonote_id in id_to_protonote:
                            selected_protonotes.append(id_to_protonote[protonote_id])

        if not selected_protonotes:
            export_input_queue.task_done()
            QMessageBox.warning(container, "Warning", "No notes selected for export")
            continue

        success = service.export_protonotes(selected_protonotes)

        if success:
            QMessageBox.information(
                container,
                "Success",
                "Successfully exported notes to Anki",
            )
        else:
            QMessageBox.warning(
                container,
                "Error",
                "Failed to export notes to Anki",
            )

        export_input_queue.task_done()


class AICardsContainer(QWidget):
    @classmethod
    @contextlib.asynccontextmanager
    async def running(
        cls,
        service: Service,
        parent: QWidget | None,
    ) -> t.AsyncIterator[t.Self]:
        async with asyncio.TaskGroup() as tg:
            self = cls(service, parent, tg)
            yield self

    def __init__(
        self,
        service: Service,
        parent: QWidget | None,
        tg: asyncio.TaskGroup,
    ) -> None:
        super().__init__(parent)
        self.service = service

        # Create widgets
        top_section = create_top_section(self)
        self._confirm_button = create_confirm_button(self)
        self._notes_tree = create_notes_preview(self)
        self._export_button = create_export_button(self)
        layout = create_main_layout(
            top_section, self._confirm_button, self._notes_tree, self._export_button
        )
        self.setLayout(layout)

        # Create queues
        _extraction_input_queue = asyncio.Queue[Image]()
        _protonote_input_queue = asyncio.Queue[t.Sequence[Extraction]]()
        _export_input_queue = asyncio.Queue[
            tuple[dict[str, Protonote], t.Sequence[ExtractionProtonotes]]
        ]()

        tg.create_task(
            paste_receiver(
                _extraction_input_queue,
                self,
            )
        )
        tg.create_task(
            extraction_handler(
                _extraction_input_queue,
                _protonote_input_queue,
                self,
                service,
            )
        )
        tg.create_task(
            protonote_handler(
                _protonote_input_queue,
                _export_input_queue,
                self,
                service,
            )
        )
        tg.create_task(
            export_handler(
                _export_input_queue,
                self,
                service,
            )
        )

    @cached_property
    def image_area(self) -> QLabel:
        return self.findChild(QLabel)

    @cached_property
    def extractions_list(self) -> QListWidget:
        return self.findChild(QListWidget)

    @property
    def confirm_button(self) -> QPushButton:
        return self._confirm_button

    @property
    def notes_tree(self) -> QTreeWidget:
        return self._notes_tree

    @property
    def export_button(self) -> QPushButton:
        return self._export_button


def create_main_layout(*widgets: QWidget) -> QVBoxLayout:
    layout = QVBoxLayout()
    for widget in widgets:
        layout.addWidget(widget)
    return layout


def create_top_section(parent: QWidget) -> QWidget:
    container = QWidget(parent)
    layout = QHBoxLayout()

    layout.addWidget(create_image_area(container))
    layout.addWidget(create_extractions_list(container))

    container.setLayout(layout)
    return container


def create_image_area(parent: QWidget) -> QLabel:
    label = QLabel("Paste screenshot with Ctrl+V", parent)
    label.setMinimumSize(400, 300)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setFrameStyle(1)  # Box | Sunken
    return label


def create_extractions_list(parent: QWidget) -> QListWidget:
    widget = QListWidget(parent)
    widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    return widget


def create_confirm_button(parent: QWidget) -> QPushButton:
    return QPushButton("Process Selected Extractions", parent)


def create_notes_preview(parent: QWidget) -> QTreeWidget:
    tree = QTreeWidget(parent)
    tree.setHeaderLabels(["Type", "Description"])
    tree.setMinimumHeight(200)
    return tree


def create_export_button(parent: QWidget) -> QPushButton:
    return QPushButton("Import into Anki database", parent)


def qt_signal_to_future(signal) -> asyncio.Future:
    """Convert a Qt signal to an asyncio future."""
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def slot(*args):
        signal.disconnect(slot)
        if not future.done():
            future.set_result(args[0] if args else None)

    signal.connect(slot)
    return future
