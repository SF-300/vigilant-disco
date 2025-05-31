import pytest

from aicards.ctx.aicards.core import Service
from aicards.ctx.aicards.base import Extraction, MeaningProtonote, EnglishNounProtonote


@pytest.fixture
def service() -> Service:
    """Provides a MockService instance for testing."""
    return Service()


@pytest.fixture
def sample_image() -> bytes:
    """Provides sample image data for testing."""
    return b"fake image data"


@pytest.fixture
def sample_extractions() -> list[Extraction]:
    """Provides sample extractions for testing."""
    return [
        Extraction(
            id="test-extract-1",
            snippet="Test content 1",
            context="Test context 1",
        ),
        Extraction(
            id="test-extract-2",
            snippet="Test content 2",
            context=None,
        ),
    ]


def test_process_image_returns_extractions(service: Service, sample_image: bytes):
    """Test that process_image returns a non-empty sequence of Extraction objects."""
    extractions = service.extract_emphases(sample_image)
    assert len(extractions) > 0
    for extraction in extractions:
        assert isinstance(extraction, Extraction)
        assert extraction.id.startswith("extract-")
        assert isinstance(extraction.snippet, str)
        assert extraction.context is None or isinstance(extraction.context, str)


def test_create_protonotes_generates_notes_for_each_extraction(
    service: Service, sample_extractions: list[Extraction]
):
    """Test that create_protonotes generates protonotes for each extraction."""
    results = service.create_protonotes(sample_extractions)

    assert len(results) == len(sample_extractions)

    for result in results:
        # Verify extraction is preserved
        assert result.extraction in sample_extractions

        # Verify protonotes are generated
        assert len(result.protonotes) == 2  # We expect 2 notes per extraction

        # Verify note types
        notes_by_type = {type(note) for note in result.protonotes}
        assert notes_by_type == {MeaningProtonote, EnglishNounProtonote}

        for note in result.protonotes:
            assert note.id.startswith("proto-")
            assert len(note.examples) > 0


def test_create_protonotes_handles_empty_input(service: Service):
    """Test that create_protonotes handles empty input gracefully."""
    results = service.create_protonotes([])
    assert len(results) == 0


def test_export_protonotes_returns_success(
    service: Service, sample_extractions: list[Extraction]
):
    """Test that export_protonotes returns True indicating success."""
    # First create some protonotes to export
    results = service.create_protonotes(sample_extractions)
    protonotes = [note for result in results for note in result.protonotes]

    # Try to export them
    assert service.export_protonotes(protonotes) is True


def test_export_protonotes_handles_empty_input(service: Service):
    """Test that export_protonotes handles empty input gracefully."""
    assert service.export_protonotes([]) is True
