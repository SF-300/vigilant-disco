import asyncio
import typing as t
from pathlib import Path

from PyQt5.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QApplication,
    QFileDialog,
)
from PyQt5.QtCore import Qt, QBuffer, QIODevice, QByteArray
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtGui import QPainter, QLinearGradient, QColor

from aicards.misc.utils import future_from_qt_signal
from aicards.ctx.aicards.base import IService, Extraction, Image

from ._base import AddLlmChatMessage


def process_image_for_display(
    qt_image: QImage,
    image_area: QPushButton,
    filename: str,
) -> Image:
    # Scale and display image
    scaled = qt_image.scaled(
        image_area.width(),
        image_area.height(),
        Qt.AspectRatioMode.KeepAspectRatio,
    )
    pixmap = QPixmap.fromImage(scaled)

    image_area.setIcon(QIcon(pixmap))
    image_area.setIconSize(pixmap.size())
    image_area.setText("")  # Hide text when showing an image

    # Convert to domain Image
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    qt_image.save(buffer, "PNG")
    buffer.close()

    return Image(
        name=filename,
        mime="image/png",
        data=bytes(byte_array.data()),
    )


async def extractions_processor(
    incoming: asyncio.Queue[Image],
    outgoing: asyncio.Queue[t.Sequence[Extraction]],
    extractions_list: QListWidget,
    confirm_button: QPushButton,
    service: IService,
    add_llm_chat_message: AddLlmChatMessage,
) -> None:
    async def pull():
        while True:
            image = await incoming.get()

            image_processing = service.process_image(image)
            async with await image_processing.llm_messages.subscribe_async(
                add_llm_chat_message
            ):
                new_extractions = await image_processing

            for extraction in new_extractions:
                item = QListWidgetItem(extraction.snippet)
                item.setData(Qt.ItemDataRole.UserRole, extraction)
                extractions_list.addItem(item)
                item.setSelected(True)

            incoming.task_done()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(pull())

        while True:
            await future_from_qt_signal(confirm_button.clicked)

            selected_extractions: list[Extraction] = []
            for item in extractions_list.selectedItems():
                extraction = item.data(Qt.ItemDataRole.UserRole)
                selected_extractions.append(extraction)

            if not selected_extractions:
                continue

            extractions_list.clear()
            await outgoing.put(selected_extractions)


async def image_file_dialog_processor(
    outgoing: asyncio.Queue[Image],
    image_area: QPushButton,
    add_llm_chat_message: AddLlmChatMessage,
) -> None:
    try:
        while True:
            # Wait for the image area to be clicked
            await future_from_qt_signal(image_area.clicked)

            # Create and show file dialog
            file_dialog = QFileDialog(
                image_area.window(),
                "Select Image",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp *.gif)",
            )
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

            # Create a future that will be completed when the dialog is finished
            # We use finished signal which is emitted when dialog is closed by any means
            finished_future = future_from_qt_signal(file_dialog.finished)

            # Show dialog non-modally
            file_dialog.open()

            # Wait for dialog to finish
            result = await finished_future

            # Check if a file was selected (dialog accepted)
            if result != QFileDialog.Accepted:
                continue

            # Get the selected file
            selected_files = file_dialog.selectedFiles()
            if not selected_files or not selected_files[0]:
                continue

            file_path = selected_files[0]

            # Process the selected file
            file_path_obj = Path(file_path)
            qt_image = QImage(str(file_path_obj))

            if qt_image.isNull():
                print(f"Failed to load image from {file_path_obj}")
                continue

            # Process image for display and conversion to domain object
            image = process_image_for_display(qt_image, image_area, file_path_obj.name)

            print(
                f"File dialog: forwarding image {file_path_obj.name} to extraction handler"
            )
            await outgoing.put(image)

    except asyncio.CancelledError:
        pass  # No cleanup needed


async def clipboard_pastes_processor(
    outgoing: asyncio.Queue[Image],
    image_area: QPushButton,
    add_llm_chat_message: AddLlmChatMessage,
) -> None:
    clipboard = QApplication.clipboard()
    assert clipboard is not None
    paste_event_queue = asyncio.Queue[QImage]()

    # TODO: Cleanups
    def handle_clipboard_change() -> None:
        mime_data = clipboard.mimeData()
        if mime_data is None or not mime_data.hasImage():
            return

        qt_image = clipboard.image()
        if qt_image.isNull():
            return

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

            # Process image for display and conversion to domain object
            image = process_image_for_display(
                qt_image, image_area, "clipboard_image.png"
            )

            print("Paste receiver: forwarding to extraction handler")
            await outgoing.put(image)
            paste_event_queue.task_done()
    finally:
        clipboard.dataChanged.disconnect(conn)
