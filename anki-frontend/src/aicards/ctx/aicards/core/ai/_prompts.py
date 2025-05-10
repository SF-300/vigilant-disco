SYSTEM_PROMPT = """
Extract text from the following image, focusing only on highlighted/emphasized German words and/or phrases.
The words and phrases can be emphasized by highlights, underlines, bold, or any other distinct visual marker. 
If multiple words are highlighted/emphasized together, consider them as a single phrase.
The exact method of emphasizing will be specified by the message accompanying the image - follow those instructions as close as possible.

If the snippet is a part of a sentence, the whole sentence should be saved in "context" field.
Otherwise, the "context" field should be empty.
Mind that sentences might span multiple lines.
Also note that images might come from textbook excercises, so it might contain different irrelevant formatting (like e.g. "(2)") that should be stripped.

"kind" must contain one of the following enum keys: {kind_keys_str}.

Normalize standalone nouns, verbs, and adjectives to their base forms if applicable.
""".strip()

