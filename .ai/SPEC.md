## MVP Specification: Anki Add-on for Creating Flashcards from Homework Screenshots

**1. Goal:**

To develop an Anki add-on that streamlines the process of creating flashcards for new English nouns encountered during homework. The add-on will allow users to take a screenshot of their homework with underlined words, extract these words, and easily create corresponding Anki notes for vocabulary learning.

**2. Target User:**

Language learners who use Anki for vocabulary acquisition and want a more efficient way to create flashcards from their study materials.

**3. Core Functionality (MVP):**

The add-on will enable users to:

* Paste a screenshot containing underlined English nouns into a dedicated Anki window.
* See a preview of the text fragments extracted from the image.
* Select the English nouns they want to create flashcards for.
* View a preview of the Anki notes that will be created for each selected noun.
* Confirm and export these notes directly into their Anki collection.

**4. User Flow:**

1.  **Capture Screenshot:** The user takes a screenshot of their homework or study material where new English nouns are underlined.
2.  **Open Dedicated Window:** The user opens a dedicated window within the Anki application provided by the add-on.
3.  **Paste Screenshot:** The user presses `Ctrl+V` to paste the screenshot into the dedicated window.
4.  **Initial Text Extraction:** The add-on utilizes an LLM API to perform OCR on the image and extracts all text fragments.
5.  **Select Target Nouns:** The add-on displays a simple multi-select list of the extracted text fragments. The user selects the English nouns they wish to create flashcards for.
6.  **Generate Note Data (LLM):** For each selected noun, the add-on uses the LLM API to:
    * Identify the sentence in the screenshot where the noun occurs.
    * Generate a concise "concept" (meaning) for the noun in that specific context.
    * Provide the singular and plural forms of the noun.
7.  **Preview Notes:** The add-on presents a nested preview (using a tree table structure) of the Anki notes that will be created:
    * **Top Level:** The selected extracted noun.
    * **Nested Items:**
        * **Meaning Note (with checkbox):**
            * Sentence: \[Extracted sentence from LLM]
            * Concept: \[Generated concept from LLM]
        * **English Noun Note (with checkbox):**
            * Singular: \[Singular form from LLM]
            * Plural: \[Plural form from LLM]
8.  **Confirm and Export:** The user reviews the preview and selects the "Meaning" and/or "English noun" notes they want to create for each word using the checkboxes. They then click an "Export to Anki" button.
9.  **Export in Progress:** The add-on's GUI grays out to indicate that the export process is running.
10. **Feedback:**
    * **Success:** Upon successful export, a message "Successfully exported the selected notes to Anki" is displayed.
    * **Error:** If an error occurs during export, a simple message "An error occurred during export. Please try again." is displayed.

**5. Anki Note Types (Pre-requisite for MVP):**

It is assumed that the following note types are already created and available in the user's Anki profile:

* **"Meaning" Note Type:**
    * Fields: `sentence`, `concept`
    * Card Template: Generates a cloze deletion card based on the `sentence` field.
* **"English noun" Note Type:**
    * Fields: `singular`, `plural`
    * Card Template: Generates two cards: one showing the singular form and asking for the plural, and another showing the plural form and asking for the singular.

**6. Technology Stack (MVP):**

* **Anki Add-on Development:** Python
* **GUI Framework:** PyQt
* **OCR and NLP:** LLM API (specific API to be determined)

**7. Error Handling (MVP):**

Basic error messages will be displayed to the user in case of issues during the export process.

**8. Future Considerations (Beyond MVP):**

* Support for German nouns (including gender).
* Allowing users to edit the extracted text and the LLM-generated information before export.
* Integration with a dictionary for more reliable word form retrieval.
* Support for other card types (e.g., vocabulary with definitions, example sentences).
* More detailed error reporting and logging.
