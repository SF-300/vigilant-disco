"""
Core implementation of the AiCards service.
"""

import uuid
import typing as t
from ..base import (
    Service,
    Extraction,
    Protonote,
    ExtractionProtonotes,
    MeaningProtonote,
    EnglishNounProtonote,
)


class MockService(Service):
    """A mock implementation of the Service interface for development and testing."""

    def process_image(
        self,
        image_data: bytes,
    ) -> t.Sequence[Extraction]:
        """
        Mock implementation that creates fake extractions from image data.

        Args:
            image_data: The raw bytes of the image

        Returns:
            A sequence of mock Extraction objects
        """
        # In a real implementation, this would process the image and extract content
        # For the mock, we'll return some predefined extractions
        return [
            Extraction(
                id=f"extract-{uuid.uuid4()}",
                snippet="Mock extracted content 1",
                context="This is a mock context for extraction 1",
            ),
            Extraction(
                id=f"extract-{uuid.uuid4()}",
                snippet="Mock extracted content 2",
                context=None,
            ),
        ]

    def create_protonotes(
        self, extractions: t.Sequence[Extraction]
    ) -> t.Sequence[ExtractionProtonotes]:
        """
        Mock implementation that creates fake protonotes from extractions.

        Args:
            extractions: A sequence of Extraction objects

        Returns:
            A sequence of ExtractionProtonotes objects containing the original
            extraction and generated protonotes
        """
        result = []
        for extraction in extractions:
            # For each extraction, create a few mock protonotes of different types
            meaning_note = MeaningProtonote(
                id=f"proto-{uuid.uuid4()}",
                type="Meaning",
                concept=extraction.snippet.split()[0]
                if extraction.snippet
                else "concept",
                examples=("Example 1", "Example 2"),
            )

            noun_note = EnglishNounProtonote(
                id=f"proto-{uuid.uuid4()}",
                type="English Noun",
                singular="card",
                plural="cards",
                examples=("Example noun usage 1", "Example noun usage 2"),
            )

            result.append(
                ExtractionProtonotes(
                    extraction=extraction, protonotes=(meaning_note, noun_note)
                )
            )

        return result

    def export_protonotes(self, protonotes: t.Sequence[Protonote]) -> bool:
        """
        Mock implementation that pretends to export protonotes.

        Args:
            protonotes: A sequence of Protonote objects to export

        Returns:
            True if the export was successful, False otherwise
        """
        # In a real implementation, this would export the protonotes to Anki
        # For the mock, we'll just log and return success
        print(f"Mock export: Would export {len(protonotes)} protonotes")
        return True
