# Refinement: Column Resizability and Date Sorting

Improve the user experience by ensuring date columns sort chronologically (DD/MM/YYYY display but Year-Month-Day logic) and by making the article description column in search results resizable and persistent.

## Proposed Changes

### [main.py](file:///c:/Users/Simone/.gemini/antigravity/scratch/gestionale-tebo/main.py)

#### [MODIFY] `ArticleSearchDialog`
- Change `self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)` to `Interactive` or remove it (since line 968 already sets `Interactive`).
- Implement `_save_column_widths` and `_restore_column_widths` methods, similar to `InvoiceDetailDialog`, but using a different prefs key (e.g., `article_search_widths`).
- Update `closeEvent` to call `_save_column_widths`.
- Update `display_results` to use `make_item` for all cells, particularly for the "Data" column, passing the raw `datetime.date` object as `raw_value` and formatting the display text as `DD/MM/YYYY`.

#### [MODIFY] `MainWindow`
- In `load_table_data`, for the "fatture" section, update the date item to use formatted text `DD/MM/YYYY` while keeping the raw date object for sorting:
  ```python
  table.setItem(i, 2, make_item(obj.data.strftime("%d/%m/%Y") if obj.data else "-", raw_value=obj.data))
  ```

#### [MODIFY] `InvoiceDetailDialog`
- Ensure any dates (if added in the future or present in headers) follow the same pattern. Currently, it only shows header labels.
- Verified that `_restore_column_widths` is already called in `load_data`.

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
