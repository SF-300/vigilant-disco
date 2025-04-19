import typing as t


# Data structure for initial text extractions from highlights
class Extraction(t.TypedDict):
    id: str
    snippet: str
    context: str | None


# Data structure for detailed Anki note data
class Protonote(t.TypedDict):
    id: str
    note_type: str
    description: str


class ExtractionProtonotes(t.TypedDict):
    extraction: Extraction
    protonotes: t.Sequence[Protonote]


class ProcessImage(t.Protocol):
    def __call__(self, image_data: bytes) -> list[Extraction]: ...


class CreateProtonotes(t.Protocol):
    def __call__(self, extractions: list[Extraction]) -> list[ExtractionProtonotes]: ...


class ExportProtonotes(t.Protocol):
    def __call__(self, protonotes: list[Protonote]) -> None: ...
