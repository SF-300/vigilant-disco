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
    QListWidgetItem,
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
    ExtractionWithPrototonotes,
)


async def paste_receiver(
    extraction_input_queue: asyncio.Queue[Image],
    image_area: QLabel,
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
            # QMessageBox.warning(container, "Error", "Processing queue is full")
            raise
        except Exception as e:
            print(f"Error handling clipboard change: {e}")

    conn = clipboard.dataChanged.connect(handle_clipboard_change)

    try:
        while True:
            print("Paste receiver: waiting for image...")
            qt_image: QImage = await paste_event_queue.get()
            print("Paste receiver: got image!")

            # Scale and display image
            scaled = qt_image.scaled(
                image_area.width(),
                image_area.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
            )
            pixmap = QPixmap.fromImage(scaled)
            image_area.setPixmap(pixmap)

            # Convert to domain Image
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            qt_image.save(buffer, "PNG")
            buffer.close()

            image = Image(
                name="clipboard_image.png",
                mime="image/png",
                data=bytes(byte_array.data()),
            )

            print("Paste receiver: forwarding to extraction handler")
            await extraction_input_queue.put(image)
            paste_event_queue.task_done()
    except asyncio.CancelledError:
        clipboard.dataChanged.disconnect(conn)


async def extractions_handler(
    incoming: asyncio.Queue[Image],
    outgoing: asyncio.Queue[t.Sequence[Extraction]],
    extractions_list: QListWidget,
    confirm_button: QPushButton,
    service: Service,
) -> None:
    async def pull():
        while True:
            image = await incoming.get()
            new_extractions = await service.process_image(image)

            for extraction in new_extractions:
                item = QListWidgetItem(extraction.snippet)
                item.setData(Qt.ItemDataRole.UserRole, extraction)
                extractions_list.addItem(item)
                item.setSelected(True)

            incoming.task_done()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(pull())

        while True:
            await qt_signal_to_future(confirm_button.clicked)

            selected_extractions: list[Extraction] = []
            for item in extractions_list.selectedItems():
                extraction = item.data(Qt.ItemDataRole.UserRole)
                selected_extractions.append(extraction)

            if not selected_extractions:
                continue

            await outgoing.put(selected_extractions)
            extractions_list.clear()


async def protonotes_creator(
    incoming: asyncio.Queue[t.Sequence[Extraction]],
    outgoing: asyncio.Queue[t.Sequence[ExtractionWithPrototonotes]],
    notes_tree: QTreeWidget,
    confirm_button: QPushButton,
    service: Service,
) -> None:
    def update_tree(
        extraction_protonotes: t.Sequence[ExtractionWithPrototonotes],
    ) -> None:
        for ep in extraction_protonotes:
            extraction_item = QTreeWidgetItem(notes_tree)  # Updated
            extraction_item.setText(0, ep.extraction.snippet)
            extraction_item.setFlags(
                extraction_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
            )
            extraction_item.setCheckState(0, Qt.CheckState.Checked)
            extraction_item.setData(0, Qt.ItemDataRole.UserRole, ep)

            for protonote in ep.protonotes:
                note_item = QTreeWidgetItem(extraction_item)
                note_item.setText(0, protonote.description)
                note_item.setFlags(note_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                note_item.setCheckState(0, Qt.CheckState.Checked)
                note_item.setData(0, Qt.ItemDataRole.UserRole, protonote)

        notes_tree.expandAll()  # Updated

    def get_selected_extraction_protonotes() -> t.Sequence[ExtractionWithPrototonotes]:
        selected = []

        for i in range(notes_tree.topLevelItemCount()):  # Updated
            top_item = notes_tree.topLevelItem(i)  # Updated
            if top_item is None:
                continue
            ep = top_item.data(0, Qt.ItemDataRole.UserRole)
            if ep and top_item.checkState(0) == Qt.CheckState.Checked:
                selected.append(ep)

        return selected

    async def pull():
        while True:
            extractions = await incoming.get()
            extraction_protonotes = await service.create_protonotes(extractions)

            # Update the tree with the results
            update_tree(extraction_protonotes)

    # Run the continuous task
    async with asyncio.TaskGroup() as tg:
        tg.create_task(pull())

        while True:
            await qt_signal_to_future(confirm_button.clicked)  # Updated

            selected_protonotes = get_selected_extraction_protonotes()
            if not selected_protonotes:
                continue

            # Forward to next stage and mark as complete
            await outgoing.put(selected_protonotes)
            incoming.task_done()

            notes_tree.clear()  # Updated


async def export_handler(
    export_q: asyncio.Queue[t.Sequence[ExtractionWithPrototonotes]],
    service: Service,
) -> None:
    while True:
        items = await export_q.get()

        await service.export_protonotes([p for ep in items for p in ep.protonotes])


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
        self._confirm_extractions = create_confirm_button(self)
        self._notes_tree = create_notes_preview(self)
        self._confirm_protonotes = create_export_button(self)
        layout = create_main_layout(
            top_section,
            self._confirm_extractions,
            self._notes_tree,
            self._confirm_protonotes,
        )
        self.setLayout(layout)

        # Create queues
        _extractions_q = asyncio.Queue[Image]()
        _protonotes_q = asyncio.Queue[t.Sequence[Extraction]]()
        _exports_q = asyncio.Queue[t.Sequence[ExtractionWithPrototonotes]]()

        # Get widget references
        image_area = self.image_area
        extractions_list = self.extractions_list
        notes_tree = self.notes_tree

        tg.create_task(
            paste_receiver(
                _extractions_q,
                image_area,
            )
        )
        tg.create_task(
            extractions_handler(
                _extractions_q,
                _protonotes_q,
                extractions_list,
                self._confirm_extractions,
                service,
            )
        )
        tg.create_task(
            protonotes_creator(
                _protonotes_q,
                _exports_q,
                notes_tree,
                self._confirm_protonotes,
                service,
            )
        )
        tg.create_task(
            export_handler(
                _exports_q,
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
