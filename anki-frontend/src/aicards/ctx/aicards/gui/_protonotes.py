import asyncio
import typing as t

from PyQt5.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
)
from PyQt5.QtCore import Qt

from aicards.misc.utils import qt_signal_to_future
from aicards.ctx.aicards.base import Service, Extraction, ExtractionWithPrototonotes


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
            extraction_item = QTreeWidgetItem(notes_tree)
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

        notes_tree.expandAll()

    def get_selected_extraction_protonotes() -> t.Sequence[ExtractionWithPrototonotes]:
        selected = []

        for i in range(notes_tree.topLevelItemCount()):
            top_item = notes_tree.topLevelItem(i)
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
            await qt_signal_to_future(confirm_button.clicked)

            selected_protonotes = get_selected_extraction_protonotes()
            if not selected_protonotes:
                continue

            # Forward to next stage and mark as complete
            await outgoing.put(selected_protonotes)
            incoming.task_done()

            notes_tree.clear()