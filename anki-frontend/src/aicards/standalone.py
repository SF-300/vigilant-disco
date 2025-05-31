import os
import asyncio
import contextlib
import sys
import logging

import qasync
from PyQt5.QtWidgets import QApplication, QMainWindow
from openai import AsyncOpenAI

from aicards.misc.logging.stdlib import StdLogger
from aicards.misc.ankiconnect_client import AnkiConnectClient
from aicards.ctx.aicards.core.ai import AiClient
from aicards.ctx.aicards.core import Service
from aicards.ctx.aicards.gui import AICardsContainer


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    logger = StdLogger(logging.getLogger("aicards"))

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

                ai_client = await stack.enter_async_context(
                    AiClient.running(AsyncOpenAI())
                )

                service = await stack.enter_async_context(
                    Service.running(
                        ai_client,
                        ankiconnect_client,
                        deck_name="Default",
                        logger=logger,
                    )
                )

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
