"""
Async client for AnkiConnect API.
"""

import json
import typing as t
from contextlib import asynccontextmanager

import httpx


# Exception Hierarchy
class AnkiConnectClientError(Exception):
    """Base exception for AnkiConnect client errors."""

    pass


class AnkiConnectConnectionError(AnkiConnectClientError):
    """Error when connecting to AnkiConnect."""

    pass


class AnkiConnectAPIError(AnkiConnectClientError):
    """Error returned by the AnkiConnect API."""

    pass


class DuplicateScopeOptions(t.TypedDict, total=False):
    """Options for duplicate scope checking."""

    deckName: str
    checkChildren: bool
    checkAllModels: bool


class NoteOptions(t.TypedDict, total=False):
    """Note options."""

    allowDuplicate: bool
    duplicateScope: str
    duplicateScopeOptions: DuplicateScopeOptions


class MediaFileBase(t.TypedDict):
    """Base class for media files."""

    filename: str
    fields: t.Sequence[str]


class MediaFileWithURL(MediaFileBase, total=False):
    """Media file with URL."""

    url: str
    skipHash: str


class MediaFileWithData(MediaFileBase, total=False):
    """Media file with data."""

    data: str
    skipHash: str


class MediaFileWithPath(MediaFileBase, total=False):
    """Media file with path."""

    path: str
    skipHash: str


MediaFile = t.Union[MediaFileWithURL, MediaFileWithData, MediaFileWithPath]


class NoteData(t.TypedDict, total=False):
    deckName: str
    modelName: str
    fields: dict[str, str]
    options: NoteOptions
    tags: t.Sequence[str]
    audio: t.Sequence[MediaFile]
    video: t.Sequence[MediaFile]
    picture: t.Sequence[MediaFile]


class AddNoteParams(t.TypedDict):
    note: NoteData


class AnkiConnectClient:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    @classmethod
    @asynccontextmanager
    async def running(
        cls, host: str = "localhost", port: int = 8765
    ) -> t.AsyncGenerator["AnkiConnectClient", None]:
        async with httpx.AsyncClient(
            base_url=f"http://{host}:{port}/",
            timeout=httpx.Timeout(10.0),
        ) as client:
            yield cls(client)

    async def _request(self, action: str, version: int = 6, **params) -> t.Any:
        """Makes a request to the AnkiConnect API."""
        payload = {"action": action, "version": version}
        if params:
            payload["params"] = params

        try:
            response = await self._client.post("", json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get("error") is not None:
                raise AnkiConnectAPIError(data["error"])

            return data.get("result")

        except httpx.RequestError as e:
            raise AnkiConnectConnectionError(
                f"Failed to connect to AnkiConnect: {e}"
            ) from e
        except json.JSONDecodeError as e:
            raise AnkiConnectClientError(f"Invalid JSON response: {e}") from e

    async def add_note(self, note: NoteData) -> int:
        result = await self._request("addNote", note=note)
        if result is None:
            raise AnkiConnectAPIError("Failed to add note")
        return result
