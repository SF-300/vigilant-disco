import asyncio
import typing as t

from PyQt5.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QApplication,
)
from PyQt5.QtCore import Qt, QBuffer, QIODevice, QByteArray
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtGui import QPainter, QLinearGradient, QColor

from aicards.misc.utils import qt_signal_to_future
from aicards.ctx.aicards.base import Service, Extraction, Image


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
