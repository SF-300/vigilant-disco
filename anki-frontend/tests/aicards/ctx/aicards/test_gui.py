import pytest
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QEvent, QMimeData
from PyQt5.QtGui import QImage, QKeyEvent, QKeySequence

from aicards.ctx.aicards.base import (
    IService,
    Extraction,
    Image,
    Protonote,
    ExtractionWithPrototonotes,
)
from aicards.ctx.aicards.gui import AICardsContainer


class TestService(IService):
    def process_image(self, image: Image) -> list[Extraction]:
        assert isinstance(image, Image)
        assert image.mime == "image/png"

        return [
            Extraction(
                id="test1", snippet="Test Extraction 1", context="Test Context 1"
            ),
            Extraction(
                id="test2", snippet="Test Extraction 2", context="Test Context 2"
            ),
        ]

    def create_protonotes(
        self, extractions: list[Extraction]
    ) -> list[ExtractionWithPrototonotes]:
        return [
            ExtractionWithPrototonotes(extraction=extraction, protonotes=())
            for extraction in extractions
        ]

    def export_protonotes(self, protonotes: list[Protonote]) -> bool:
        return True


@pytest.fixture
def test_service() -> IService:
    return TestService()


@pytest.mark.qasync
async def test_paste_handling(qtbot):
    # Create test image
    test_image = QImage(100, 100, QImage.Format.Format_RGB32)
    test_image.fill(Qt.GlobalColor.white)

    # Set up clipboard with test image
    clipboard = QApplication.clipboard()
    assert clipboard is not None
    clipboard.setImage(test_image)

    # Create container
    service = TestService()
    container = AICardsContainer(service, None)
    qtbot.addWidget(container)

    # Verify initial state
    assert container.image_area.pixmap() is None
    assert container.extractions_list.count() == 0

    # Simulate Ctrl+V event
    event = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_V,
        Qt.KeyboardModifier.ControlModifier,
        QKeySequence.StandardKey.Paste,
    )
    container.eventFilter(container, event)

    # Verify image was processed
    assert container.image_area.pixmap() is not None
    assert container.extractions_list.count() == 2
    assert container.extractions_list.item(0).text() == "Test Extraction 1"
    assert container.extractions_list.item(1).text() == "Test Extraction 2"
