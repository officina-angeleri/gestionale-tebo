# Plan: Database Path Management

Allow users to see and change the active database file through the application interface.

## Proposed Changes

### [MainWindow](file:///c:/Users/Simone/.gemini/antigravity/scratch/gestionale-tebo/main.py)

#### [MODIFY] [main.py](file:///c:/Users/Simone/.gemini/antigravity/scratch/gestionale-tebo/main.py)
- **Initialization**:
    - Update `MainWindow.__init__` to load `db_path` from `self.prefs` if available.
- **Dashboard View**:
    - Add `self.db_info_label` in `setup_dashboard_view` to show the active file.
    - Update label in `load_stats` to include the current path.
- **Settings View**:
    - Add a new "Database" `QGroupBox`.
    - Add a button "📂 Seleziona Database..." to open `QFileDialog`.
- **Logic**:
    - Implement `change_db_path()`:
        - Opens `QFileDialog` filtering for `.db` files.
        - If selected, calls `self.reconnect_db(new_path)`.
    - Implement `reconnect_db(path)`:
        - Checks if the file exists.
        - Creates a new `DatabaseManager(path)`.
        - Updates `self.db_manager`.
        - Saves the path in `prefs["db_path"]`.
        - Refreshes stats and current view.

## Verification Plan

### Manual Verification
- **Path Display**: Verify the current path is visible on the Dashboard.
- **Change Path**:
    1. Go to Settings -> Change Database.
    2. Select a different `.db` file (e.g. a backup).
    3. Verify Dashboard shows the new path and stats update accordingly.
- **Error Handling**: Try selecting a non-database file (if filter allows) or verify behavior if file is missing.
- **Persistence**: Restart the app and verify it connects to the last selected database.
