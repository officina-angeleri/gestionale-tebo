# Refinement: Column Resizability, Date Sorting, and Search Fields

Improve the user experience by ensuring date columns sort chronologically, making the article search results columns resizable, and allowing field selection in the article search.

## Proposed Changes

### [main.py](file:///c:/Users/Simone/.gemini/antigravity/scratch/gestionale-tebo/main.py)

#### [MODIFY] Imports
- Add `QCheckBox` to `PySide6.QtWidgets` imports.

#### [MODIFY] `ArticleSearchDialog`
- **UI UPDATES**:
    - Add `self.cb_code = QCheckBox("Codice articolo")` and `self.cb_desc = QCheckBox("Descrizione articolo")`.
    - Set both to `Checked` by default.
    - Add them to a horizontal layout below the search bar.
- **LOGIC UPDATES**:
    - Modify `perform_search` to build `conditions` based on checkbox states.
    - If `cb_code` is checked, include `articolo_codice` in the `or_` for each word.
    - If `cb_desc` is checked, include `descrizione` in the `or_` for each word.
    - If neither is checked, default to searching both (effectively treating it as both checked).

## Verification Plan

### Automated Tests
- Run `main.py` and:
  1. Open `Ricerca Articolo` (Magnifying glass in Fatture list or similar).
  2. Test search with only "Codice articolo" checked (e.g., search for a known code).
  3. Test search with only "Descrizione articolo" checked (e.g., search for a common word like "Vite").
  4. Test with both checked.
  5. Test with neither checked (should behave like both checked).
  6. Verify that column widths and sorting still work as before.

### Manual Verification
- Confirm that the UI for field selection is compact and clear.

## Verification Plan

### Automated Tests
- Run `main.py` and:
  1. Open `Articoli` tab, search for something (or wait till it loads if it's the main view).
  2. Open an Invoice Detail -> Check sorting of rows (though rows don't have dates).
  3. Open `Fatture` tab -> Click on "Data" header -> Verify chronological sorting.
  4. Open `Ricerca Articolo` (presumably a button in Settings or Dashboard? I should find the trigger).
     - Search for an article.
     - Try resizing "Descrizione Articolo" column.
     - Close and reopen -> Width should be preserved.
     - Click on "Data" header in search results -> Verify chronological sorting.

### Manual Verification
- Confirm with user that "DD/MM/YYYY" is the preferred display format for all dates.
