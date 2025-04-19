# MVP Specification: Anki Add-on for Creating Flashcards from Homework Screenshots

## Goal

To develop an Anki add-on that streamlines the process of creating flashcards from text fragments **highlighted** by the user in their homework. The add-on will allow users to take a screenshot containing these **highlights**, identify text **extractions** from those areas, and easily create corresponding Anki notes.

## Target User

Language learners who use Anki for vocabulary acquisition and want a more efficient way to create flashcards from their **highlighted** study materials.

## Core Functionality (MVP)

The add-on will enable users to:

* Paste a screenshot containing **highlighted** words, phrases, grammatical constructions, ... into a dedicated Anki window.
* See a preview of the text **extractions** identified from the image (guided by the **highlights**).
* Select the **extractions** they want to create flashcards for.
* View a preview of the Anki notes that will be created for each selected **extraction**.
* Confirm and export these notes directly into their Anki collection.

## User Interface (UI)

The proposed user interface for the Anki add-on, based on the provided sketch, is designed within a dedicated window and guides the user through the workflow via distinct sections:

1.  **Image Display Area (Step #1):**
    * **Location:** Top-left section of the window.
    * **Purpose:** Displays the screenshot pasted by the user (via `Ctrl+V`), showing the original **highlights** and providing visual context.

2.  **Extractions List (Step #2):**
    * **Location:** Top-right section, adjacent to the Image Display Area.
    * **Purpose:** Shows the text **extractions** (nouns, phrases, phrasal verbs, ...) identified by OCR, guided by the **highlights** in the pasted image.
    * **Interaction:** Functions as a multi-select list where the user chooses the **extractions** to be used as seeds for different Anki notes.

3.  **Confirmation Action (Step #3):**
    * **Location:** Positioned between the Extractions List and the Note Preview & Selection Area.
    * **Component:** A "**Confirm**" button.
    * **Purpose:** Triggers LLM processing (context, concept, grammatical forms, ...) for the **extractions** selected in the Extractions List.

4.  **Note Preview & Selection Area (Step #4):**
    * **Location:** The main, larger area below the Image Display and Confirmation Action.
    * **Structure:** Organized as a tree table or an expandable list.
    * **Content:**
        * **Top Level:** Lists each **extraction** selected from the Extractions List (e.g., `+ Electricity`, `+ drinking`).
        * **Nested Levels:** Expanding an **extraction** reveals potential Anki notes, for which this particular **extraction** should be used as seed:
            * **Grammar:** Shows data for the `"English Noun"` note type in Phase 1 MVP (singular/plural forms and examples). The interface is designed to accommodate additional grammar types in future phases.
            * **Meaning:** Shows data for the `"Meaning"` note type (Term/Concept and Example Sentences).
    * **Interaction (Implied by SPEC):** Treetable here has selectable rows to allow users to select precisely which note types to export for each chosen **extraction**.

5.  **Final Export Action (Sketch #5):**
    * **Location:** At the bottom of the window.
    * **Component:** An "**Import into Anki database**" button.
    * **Purpose:** Initiates the export of the user-selected notes (from the Preview Area) into their Anki collection.

## User Flow

1.  **Highlight & Capture Screenshot:** The user **highlights** text fragments in their homework or study material and takes a screenshot.
2.  **Open Dedicated Window:** The user opens the dedicated add-on window within Anki.
3.  **Paste Screenshot:** The user presses `Ctrl+V`; the screenshot (showing the **highlights**) appears in the **Image Display Area (1)**.
4.  **Initial Text Extraction:** The add-on utilizes an LLM API to perform OCR on the image, focusing on the **highlighted** areas, and populates the **Extractions List (2)** with the identified text **extractions**.
5.  **Select Target Extractions:** The user selects the **extractions** they wish to create flashcards for from the **Extractions List (2)**.
6.  **Confirm Selections:** The user clicks the **Confirm button (3)**.
7.  **Generate & Display Note Data (LLM):** For each selected **extraction**, the add-on uses the LLM API to:
    * Identify the sentence in the screenshot where the **extraction** occurs (within the context of the original **highlight**).
    * Determine the grammatical type of the **extraction** (e.g., English noun, verb, phrase, ...).
    * Generate a concise "concept" (meaning) for the **extraction** in that specific context.
        * It might be simply a defaul form for nouns (signular, nominative), verbs (infinitive), ...
        * For phrases, it might be some concise description of the meaning in this particular context
      * For English nouns (Phase 1 MVP): Generate singular and plural forms.
    * Generate up to 5 example sentences showcasing the **extraction** in context.
    The add-on then displays this data in the **Note Preview & Selection Area (4)**, structured as described in the UI section.
8.  **Review & Select Notes:** The user reviews the generated data in the **Note Preview & Selection Area (4)**, using the expandable structure to finalize selections (e.g., "Meaning", "Grammar") for each **extraction**.
9.  **Initiate Export:** The user clicks the **Import into Anki database button (5)**.
10. **Export in Progress:** The add-on's GUI grays out to indicate that the export process is running.
11. **Feedback:**
    * **Success:** Upon successful export, a message "Successfully exported the selected notes to Anki" is displayed in the UI.
    * **Error:** If an error occurs during export, a simple message "An error occurred during export. Please try again." is displayed in the UI.

## Anki Note Types

It is assumed that the following note types are already created and available in the user's Anki profile:

### "Meaning" Note Type
* Fields: 
    * `concept`
    * `example1`, `example2`, `example3`, `example4`, `example5` (example sentences)
* Card Template: Generates a cloze deletion card based on the `example*` fields.

### "English Noun" Grammar Note Type
* Fields:
    * `singular`, `plural`
    * `example1`, `example2`, `example3`, `example4`, `example5` (examples using the noun)
* Card Template: Cards for practicing noun forms with examples

## Technology Stack (MVP)

* **Anki Add-on Development:** Python
* **GUI Framework:** PyQt
* **OCR and NLP:** LLM API

## Architecture & Code Organization

* The project follows a **Domain-Driven Design (DDD)** approach with a single bounded context: `aicards`.
* The codebase is organized into vertical slices:
    * **base:** Contains shared data structures and interfaces (using Python protocols) for dependency inversion.
    * **core:** Contains business logic, including all interactions with the Anki API and the LLM API, implemented against interfaces defined in `base`.
    * **gui:** Implements the PyQt GUI, orchestrates user interactions, and communicates with `core` using objects and interfaces defined in `base`.
* All dependencies between layers are explicit and follow dependency inversion principles—hidden dependencies are avoided.
* Data exchanged between `gui` and `core` is represented by complex objects (e.g., dataclasses) defined in `base`.
* Modern Python (>=3.13) features are used throughout the codebase (e.g., `list[str]` instead of `typing.List[str]`).

## Future Considerations (Beyond MVP)

* Support for German nouns (including gender).
* Allowing users to edit the extracted text and the LLM-generated information before export.
* Integration with a dictionary for more reliable word form retrieval.
* Support for other card types (e.g., vocabulary with definitions, example sentences).
* More detailed error reporting and logging.
