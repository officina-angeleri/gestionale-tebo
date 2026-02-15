# Refinement: Column Resizability, Date Sorting, Search Fields, Quick Actions, and Incremental Search

Improve the user experience by ensuring date columns sort chronologically, making the article search results columns resizable, allowing field selection in the article search, adding quick actions like double-click to open details, and enabling incremental search.

## Proposed Changes

### [main.py](file:///c:/Users/Simone/.gemini/antigravity/scratch/gestionale-tebo/main.py)

#### [MODIFY] `ArticleSearchDialog`
- **UI UPDATES**:
    - Add `self.cb_incremental = QCheckBox("Ricerca incrementale")` in the options layout.
    - Add `self.lbl_mode = QLabel("Modalità: Nuova ricerca")` to indicate current state.
    - Connect `self.cb_incremental.stateChanged` to update `self.lbl_mode`.
- **LOGIC UPDATES**:
    - Initialize `self.active_search_steps = []` in `__init__`.
    - In `perform_search`:
        - Construct a search step object: `{'words': text.split(), 'code': cb_code.isChecked(), 'desc': cb_desc.isChecked()}`.
        - If NOT Incremental: `self.active_search_steps = [current_step]`.
        - If Incremental: `self.active_search_steps.append(current_step)`.
        - Rebuild the SQLAlchemy query by iterating over `self.active_search_steps`, adding an `AND` filter block for each step (which contains its own `OR` logic for fields).
- **UX**:
    - Update the status label to show if it's a filtered subset or a fresh search.

## Verification Plan

### Automated Tests
- Run `main.py` and:
  1. Open `Ricerca Articolo`.
  2. Perform a search.
  3. Double-click on any part of a result row.
  4. Verify that the correct `InvoiceDetailDialog` opens.
  5. Verify that the "Dettaglio Fattura" button still works.

### Manual Verification
- Confirm that the double-click feels responsive and consistent with other tables in the app (like the main Invoices table).

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
