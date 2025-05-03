import asyncio
import contextlib
import sys

import qasync
from PyQt5.QtWidgets import QApplication, QMainWindow

from aicards.misc.utils import iife
from aicards.misc.ankiconnect_client import AnkiConnectClient
from aicards.ctx.ankiconnect import notedata_from
from aicards.ctx.aicards.core import MockService
from aicards.ctx.aicards.gui import AICardsContainer


def main() -> None:
    app = QApplication(sys.argv)

    loop = qasync.QEventLoop(app)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    main_window = QMainWindow()
    main_window.setWindowTitle("AI Cards Standalone")
    main_window.resize(800, 600)

    with loop:

        async def driver():
            async with contextlib.AsyncExitStack() as stack:
                ankiconnect_client = await stack.enter_async_context(
                    AnkiConnectClient.running()
                )

                @iife
                class service(MockService):
                    async def export_protonotes(self, protonotes):
                        for protonote in protonotes:
                            note_data = notedata_from(protonote, deck_name="English")
                            await ankiconnect_client.addNote(note_data)

                container = await stack.enter_async_context(
                    AICardsContainer.running(
                        service,
                        main_window,
                    )
                )
                main_window.setCentralWidget(container)
                main_window.show()
                await app_close_event.wait()

        loop.run_until_complete(driver())


if __name__ == "__main__":
    main()
