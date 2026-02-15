# Refinement: Column Resizability, Date Sorting, Search Fields, and Quick Actions

Improve the user experience by ensuring date columns sort chronologically, making the article search results columns resizable, allowing field selection in the article search, and adding quick actions like double-click to open details.

## Proposed Changes

### [main.py](file:///c:/Users/Simone/.gemini/antigravity/scratch/gestionale-tebo/main.py)

#### [MODIFY] `ArticleSearchDialog`
- **UI UPDATES**:
    - Connect `self.table.cellDoubleClicked` to a new method `handle_double_click`.
- **LOGIC UPDATES**:
    - In `display_results`, set `user_role_data=riga.fattura` for the first column item using `make_item`.
    - Implement `handle_double_click(self, row, column)` to retrieve the `fattura` object from the row's first item and call `self.open_invoice_detail(fattura)`.

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
