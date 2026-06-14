# Mined Words Translation Injection Workflow & Technical Documentation

## 1. Workflow Instructions

* **Step 1:** Select a chapter that has already been read.
* **Step 2:** Search for all words in Anki that were mined for it. Make sure that you only select from the card type "pronunciation" to avoid duplicate words, and do not take the suspended grammar cards.
* **Step 3:** Extract with the extraction addon only the word, the sentence plain, the English and potentially the Japanese overview, and the Note ID (`nid`) as HTML.
* **Step 4:** Put the table into Google Sheets or Excel.
* **Step 5:** Provide the exported table as a TSV to the AI and write the following prompt:
    > "I want you to output a list below (i.e., a TSV (tab separated file) with only one column) and that as a copy-paste text block here.
    > I want you to analyze the table below—the word, the definition overview (English, Japanese), and the example sentence.
    > And I want you to tell me (maximum of 4 words) what the appropriate definition in context is per line."
* **Step 5.5:** You can import the generated "short translations" back into Anki with the injection extraction addon. You select the cards you chose before again, inject the short translations with the revised TSV that you exported from Excel or Google Sheets as a TSV again (you select in the addon that you want to import it as HTML and the field `Correct English Definition`, and match with the `nids` after you have selected the TSV in the explorer dialog).
* **Step 6:** After the AI has generated the list, you insert it as a new column into the table you extracted earlier. You then feed this table as a TSV into the Python script `minedwordstranslationinjection.py`. Additionally, you provide the `.ass` file with the corresponding chapter you were interested in.
* **Step 7:** The subtitle file of the chapter is now provided with the desired meanings of the words, and you can watch it by playing it with the audio.

---

## 2. Technical Documentation: minedwordstranslationinjection.py

### Input / Output Perspective
* **Execution Environment:** Independent execution environment managed through cross-platform graphical user interface (`tkinter`) file explorer dialogs for file selection.
* **Input Files & Location:**
    * **Tabular File (TSV/CSV):** A spreadsheet containing vocabulary data, loaded dynamically with automatic delimiter detection supporting tabs, semicolons, or commas.
    * **ASS Subtitle File:** An Advanced SubStation Alpha subtitle template containing time-synced dialogue lines.
* **Output Files & Location:**
    * **Updated ASS Subtitle File:** Modifies and overwrites the source `.ass` file directly, injecting custom color formatting and positional definitions.
* **Concrete Input Format:**
    * *Table Columns:* Must include three strictly named columns: `Word`, `SentencePlain`, and `Kontextuelle_Definition`.
    * *ASS Lines:* Filters and modifies entries belonging to the `Text` style layer that start with the standard `Dialogue:` prefix.

---

### Core Architecture & Specifications

#### Functionality
The script processes subtitle documents to visually highlight target vocabulary terms and dynamically inject floating contextual definitions directly above the dialogue lines.

#### Operation
1. The script initializes a hidden root window to launch explorer dialogs.
2. The user selects the vocabulary table file and the target `.ass` file sequentially.
3. The table data is validated, unique bright colors are generated for text consistency, and the subtitle file is updated and rewritten.

#### Logic
* **Text Normalization Engine:** A robust cleaning function strips structural formatting syntax, positioning configurations (`\pos`), hard-coded line breaks (`\N`, `\n`), blank spaces, and Japanese/German punctuation characters to guarantee accurate substring matching.
* **Consistent Color Binding:** Generates random bright colors using the ASS hex scheme (`BBGGRR`) and maps them deterministically to specific word-sentence pairs to preserve visual identity across frames.
* **Contextual Matching:** Cross-references lines by confirming that the normalized TSV example sentence exists within the cleaned subtitle text, and that the raw target word is present inside the dialogue block.
* **Substring Overlap Resolution:** Sorts matched items by word length in descending order before execution to prevent shorter sub-words from breaking nested or longer terms during replacement.
* **Chronological Appearance Sorting:** Organizes multiple definitions according to their exact appearance index within the original text to maintain natural reading order in the display block.
* **Dynamic Layout Positioning:** Locates the original `\pos(X,Y)` positioning tags and shifts the vertical coordinate (`Y - 100`) to render a separate line containing the combined definitions side-by-side above the main dialogue.
