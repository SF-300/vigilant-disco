import typing as t
import functools

from aicards.misc.ankiconnect_client import NoteData
from aicards.ctx.aicards.base import Protonote, EnglishNounProtonote, MeaningProtonote


@functools.singledispatch
def notedata_from(
    protonote: Protonote,
    deck_name: str = "Default",
    tags: t.Sequence[str] = tuple(),
) -> NoteData:
    raise NotImplementedError(f"Unsupported protonote type: {type(protonote)}")


@notedata_from.register
def _(
    protonote: MeaningProtonote,
    deck_name: str = "Default",
    tags: t.Sequence[str] = tuple(),
) -> NoteData:
    # Create fields dictionary with proper Anki field names
    fields = {"Concept": protonote.concept}

    # Add examples to fields with correct field names
    for i, example in enumerate(protonote.examples, 1):
        if example:
            fields[f"Example {i} Sentence"] = example.sentence

    return {
        "deckName": deck_name,
        "modelName": protonote.type,
        "fields": fields,
        "tags": tags,
    }


@notedata_from.register
def _(
    protonote: EnglishNounProtonote,
    deck_name: str = "Default",
    tags: t.Sequence[str] = tuple(),
) -> NoteData:
    fields = {
        "Singular": protonote.singular,
        "Plural": protonote.plural,
    }

    return {
        "deckName": deck_name,
        "modelName": protonote.type,
        "fields": fields,
        "tags": tags,
    }
