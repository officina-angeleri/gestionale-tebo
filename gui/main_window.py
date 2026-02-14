from PySide6.QtWidgets import QMainWindow, QTabWidget, QMessageBox, QToolBar, QStatusBar
from PySide6.QtGui import QAction
from gui.views import TableViewWidget
from data_manager import DataManager
from database import DatabaseManager
import threading

class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.setWindowTitle("Gestionale Tebo")
        self.resize(1024, 768)
        self.db_manager = db_manager # database.DatabaseManager instance
        
        self.init_ui()

    def init_ui(self):
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        import_action = QAction("Importa Excel", self)
        import_action.triggered.connect(self.run_import)
        toolbar.addAction(import_action)

        # Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Database Connection for Qt
        # Note: DatabaseManager uses SQLAlchemy, but QSqlTableModel needs QSqlDatabase
        # We assume the connection is already set up in main.py globally or passed here
        from PySide6.QtSql import QSqlDatabase
        self.qt_db = QSqlDatabase.database()

        self.tabs.addTab(TableViewWidget("clienti", self.qt_db), "Clienti")
        self.tabs.addTab(TableViewWidget("fornitori", self.qt_db), "Fornitori")
        self.tabs.addTab(TableViewWidget("articoli", self.qt_db), "Articoli")
        self.tabs.addTab(TableViewWidget("righe_vendita", self.qt_db), "Vendite")

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    def run_import(self):
        reply = QMessageBox.question(self, "Conferma Importazione", 
                                     "L'importazione potrebbe richiedere del tempo. Vuoi procedere?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.statusBar.showMessage("Importazione in corso...")
            # Run in thread to allow UI to update (though simple thread might not update UI safely without signals)
            # For simplicity in this plan, we run synchronous or pseudo-thread
            try:
                dm = DataManager(self.db_manager)
                dm.import_all()
                QMessageBox.information(self, "Successo", "Importazione completata!")
                self.statusBar.showMessage("Importazione completata.")
                # Refresh tabs
                for i in range(self.tabs.count()):
                    self.tabs.widget(i).refresh()
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante l'importazione: {str(e)}")
                self.statusBar.showMessage("Errore Importazione.")
