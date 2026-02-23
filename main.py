from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLineEdit, QFrame, 
                             QMessageBox, QStackedWidget, QGridLayout, QComboBox,
                             QFormLayout, QGroupBox, QStatusBar, QDialog, QFileDialog,
                             QDateEdit, QCheckBox, QTabWidget, QTextEdit)
from PySide6.QtCore import Qt, QSize, QDate, QUrl
from PySide6.QtGui import QFont, QAction, QColor, QPixmap, QIcon, QDesktopServices
from database import DatabaseManager, Cliente, Fornitore, Articolo, Fattura, RigaFattura
from data_manager import DataManager
import sys
import os
import json
import base64
import subprocess
import winreg
from io import BytesIO
from sqlalchemy import or_, and_, extract
from sqlalchemy.orm import joinedload

# Path for column preferences file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COLUMN_PREFS_FILE = os.path.join(BASE_DIR, "column_prefs.json")

# Lista predefinita fornitori da escludere (utenze, GDO, telecom, ecc.)
FORNITORI_SERVIZIO_DEFAULT = [
    "TIM", "TELECOM", "ENEL", "ENI", "A2A", "IREN", "HERA", "ITALGAS",
    "VODAFONE", "WIND", "FASTWEB", "TISCALI", "ILIAD", "3 ITALIA",
    "ESSELUNGA", "CARREFOUR", "CONAD", "COOP", "LIDL", "ALDI", "EUROSPIN",
    "PENNY", "PAM", "SIGMA", "DESPAR", "SPAR", "MD", "IN'S",
    "AMAZON", "EBAY", "PAYPAL",
]


def load_column_prefs():
    """Load column visibility preferences from JSON file."""
    if os.path.exists(COLUMN_PREFS_FILE):
        try:
            with open(COLUMN_PREFS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_column_prefs(prefs):
    """Save column visibility preferences to JSON file."""
    with open(COLUMN_PREFS_FILE, 'w', encoding='utf-8') as f:
        json.dump(prefs, f, indent=2, ensure_ascii=False)


def save_column_order(table, key):
    """Save the visual order of columns for a specific table key."""
    header = table.horizontalHeader()
    count = header.count()
    order = [header.logicalIndex(v) for v in range(count)]
    
    prefs = load_column_prefs()
    prefs[f"order_{key}"] = order
    save_column_prefs(prefs)


def restore_column_order(table, key):
    """Restore the visual order of columns from preferences."""
    prefs = load_column_prefs()
    order = prefs.get(f"order_{key}")
    if not order or len(order) != table.columnCount():
        return
        
    header = table.horizontalHeader()
    # To restore correctly, we move each logical section to its visual index
    for v, logical_idx in enumerate(order):
        header.moveSection(header.visualIndex(logical_idx), v)


class ColumnConfigDialog(QDialog):
    """Dialog to choose which columns are visible in a table."""
    def __init__(self, columns, visible_columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configura Colonne")
        self.setMinimumWidth(300)
        self.columns = columns
        self.checkboxes = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Seleziona le colonne da visualizzare:"))

        from PySide6.QtWidgets import QCheckBox
        for col in columns:
            cb = QCheckBox(col)
            cb.setChecked(col in visible_columns)
            self.checkboxes.append(cb)
            layout.addWidget(cb)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_all = QPushButton("Seleziona Tutte")
        btn_none = QPushButton("Deseleziona Tutte")
        btn_ok = QPushButton("OK")
        btn_ok.setStyleSheet("background-color: #00bcd4; color: #000; font-weight: bold;")

        btn_all.clicked.connect(lambda: [cb.setChecked(True) for cb in self.checkboxes])
        btn_none.clicked.connect(lambda: [cb.setChecked(False) for cb in self.checkboxes])
        btn_ok.clicked.connect(self.accept)

        btn_layout.addWidget(btn_all)
        btn_layout.addWidget(btn_none)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def get_visible_columns(self):
        return [col for col, cb in zip(self.columns, self.checkboxes) if cb.isChecked()]


class SortableItem(QTableWidgetItem):
    """Custom QTableWidgetItem that sorts by a raw value stored in UserRole+1.
    Supports numeric, date, and text sorting transparently."""
    def __lt__(self, other):
        raw_self = self.data(Qt.UserRole + 1)
        raw_other = other.data(Qt.UserRole + 1) if other else None
        # If both have raw values, compare them directly
        if raw_self is not None and raw_other is not None:
            try:
                return raw_self < raw_other
            except TypeError:
                return str(raw_self) < str(raw_other)
        # Fallback to text comparison
        return (self.text() or "") < (other.text() or "")


def make_item(display_text, raw_value=None, user_role_data=None):
    """Create a SortableItem with display text and optional raw sort value."""
    item = SortableItem(str(display_text) if display_text else "")
    if raw_value is not None:
        item.setData(Qt.UserRole + 1, raw_value)
    else:
        # Try to infer a numeric value from the display text for sorting
        item.setData(Qt.UserRole + 1, display_text)
    if user_role_data is not None:
        item.setData(Qt.UserRole, user_role_data)
    return item


class CrossReferenceDialog(QDialog):
    """Ricerca incrociata di un articolo tra fatture acquisto, vendita e anagrafica."""

    def __init__(self, codice, descrizione, riga_data=None, parent=None):
        super().__init__(parent)
        self.codice = codice or ""
        self.descrizione = descrizione or ""
        self.riga_data = riga_data or {}  # {'prezzo_unitario': ..., 'quantita': ..., 'totale_riga': ...}

        # Risali a MainWindow per accedere al db_manager
        self.main_win = parent
        while self.main_win and not hasattr(self.main_win, 'db_manager'):
            self.main_win = self.main_win.parent()

        self.setWindowTitle(f"Cross-Reference: {self.codice} — {self.descrizione[:60]}")
        self.resize(900, 560)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Intestazione
        hdr = QLabel(f"🔍  <b>{self.codice}</b>  —  {self.descrizione}")
        hdr.setStyleSheet("font-size: 15px; color: #00bcd4; margin: 6px;")
        hdr.setTextFormat(Qt.RichText)
        layout.addWidget(hdr)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ── Tab Acquisti ──
        self.tab_acq = QWidget()
        acq_layout = QVBoxLayout(self.tab_acq)
        self.tbl_acq = QTableWidget()
        self.tbl_acq.setColumnCount(6)
        self.tbl_acq.setHorizontalHeaderLabels(["Data", "Fornitore", "N° Fatt.", "Qtà", "Prezzo Acq.", "Tot. Riga"])
        self.tbl_acq.horizontalHeader().setStretchLastSection(True)
        self.tbl_acq.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_acq.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_acq.setSortingEnabled(True)
        acq_layout.addWidget(self.tbl_acq)
        self.lbl_acq_summary = QLabel()
        self.lbl_acq_summary.setStyleSheet("color: #aaa; font-size: 12px; margin: 4px;")
        acq_layout.addWidget(self.lbl_acq_summary)
        self.tabs.addTab(self.tab_acq, "🛒 Acquisti")

        # ── Tab Vendite ──
        self.tab_vend = QWidget()
        vend_layout = QVBoxLayout(self.tab_vend)
        self.tbl_vend = QTableWidget()
        self.tbl_vend.setColumnCount(6)
        self.tbl_vend.setHorizontalHeaderLabels(["Data", "Cliente", "N° Fatt.", "Qtà", "Prezzo Vend.", "Tot. Riga"])
        self.tbl_vend.horizontalHeader().setStretchLastSection(True)
        self.tbl_vend.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_vend.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_vend.setSortingEnabled(True)
        vend_layout.addWidget(self.tbl_vend)
        self.lbl_vend_summary = QLabel()
        self.lbl_vend_summary.setStyleSheet("color: #aaa; font-size: 12px; margin: 4px;")
        vend_layout.addWidget(self.lbl_vend_summary)
        self.tabs.addTab(self.tab_vend, "💰 Vendite")

        # ── Tab Anagrafica ──
        self.tab_ana = QWidget()
        self.ana_layout = QVBoxLayout(self.tab_ana)
        self.tabs.addTab(self.tab_ana, "📦 Anagrafica")

        # Chiudi
        btn_close = QPushButton("✖ Chiudi")
        btn_close.clicked.connect(self.close)
        btn_close.setFixedHeight(32)
        btn_close.setStyleSheet("background-color: #444; color: #ccc; padding: 0 20px; border-radius: 4px;")
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

    def load_data(self):
        if not self.main_win: return
        session = self.main_win.db_manager.get_session()
        try:
            # Query acquisti
            acquisti = (session.query(RigaFattura)
                .join(Fattura)
                .filter(Fattura.tipo == 'ACQUISTO',
                        RigaFattura.articolo_codice == self.codice)
                .options(joinedload(RigaFattura.fattura))
                .order_by(Fattura.data.desc())
                .all())

            # Query vendite
            vendite = (session.query(RigaFattura)
                .join(Fattura)
                .filter(Fattura.tipo == 'VENDITA',
                        RigaFattura.articolo_codice == self.codice)
                .options(joinedload(RigaFattura.fattura))
                .order_by(Fattura.data.desc())
                .all())

            # Anagrafica
            articolo = session.query(Articolo).filter_by(codice=self.codice).first()

            self._populate_acquisti(acquisti)
            self._populate_vendite(vendite)
            self._populate_anagrafica(articolo)

            # Aggiorna titoli tab con conteggi
            self.tabs.setTabText(0, f"🛒 Acquisti ({len(acquisti)})")
            self.tabs.setTabText(1, f"💰 Vendite ({len(vendite)})")
            self.tabs.setTabText(2, "📦 Anagrafica" if articolo else "📦 Anagrafica ⚠")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Errore", str(e))
        finally:
            session.close()

    def _populate_acquisti(self, righe):
        self.tbl_acq.setRowCount(len(righe))
        tot_q, tot_val = 0.0, 0.0
        for i, r in enumerate(righe):
            ft = r.fattura
            self.tbl_acq.setItem(i, 0, QTableWidgetItem(str(ft.data) if ft.data else "-"))
            self.tbl_acq.setItem(i, 1, QTableWidgetItem(ft.fornitore_denominazione or ft.fornitore_codice or "-"))
            self.tbl_acq.setItem(i, 2, QTableWidgetItem(str(ft.numero) if ft.numero else "-"))
            q = r.quantita or 0.0
            pu = r.prezzo_unitario or 0.0
            tr = r.totale_riga or 0.0
            self.tbl_acq.setItem(i, 3, QTableWidgetItem(f"{q:.2f}"))
            self.tbl_acq.setItem(i, 4, QTableWidgetItem(f"€ {pu:.4f}"))
            self.tbl_acq.setItem(i, 5, QTableWidgetItem(f"€ {tr:.2f}"))
            tot_q += q
            tot_val += tr
        self.lbl_acq_summary.setText(
            f"Totale righe acquisto: {len(righe)} — Qtà totale: {tot_q:.2f} — Valore totale: € {tot_val:.2f}")

    def _populate_vendite(self, righe):
        self.tbl_vend.setRowCount(len(righe))
        tot_q, tot_val = 0.0, 0.0
        for i, r in enumerate(righe):
            ft = r.fattura
            self.tbl_vend.setItem(i, 0, QTableWidgetItem(str(ft.data) if ft.data else "-"))
            self.tbl_vend.setItem(i, 1, QTableWidgetItem(ft.cliente_denominazione or ft.cliente_codice or "-"))
            self.tbl_vend.setItem(i, 2, QTableWidgetItem(str(ft.numero) if ft.numero else "-"))
            q = r.quantita or 0.0
            pu = r.prezzo_unitario or 0.0
            tr = r.totale_riga or 0.0
            self.tbl_vend.setItem(i, 3, QTableWidgetItem(f"{q:.2f}"))
            self.tbl_vend.setItem(i, 4, QTableWidgetItem(f"€ {pu:.4f}"))
            self.tbl_vend.setItem(i, 5, QTableWidgetItem(f"€ {tr:.2f}"))
            tot_q += q
            tot_val += tr
        self.lbl_vend_summary.setText(
            f"Totale righe vendita: {len(righe)} — Qtà totale: {tot_q:.2f} — Valore totale: € {tot_val:.2f}")

    _UM_OPTIONS = ["", "nr", "mt", "kg", "lt", "conf"]

    def _populate_anagrafica(self, articolo):
        # Svuota layout
        while self.ana_layout.count():
            child = self.ana_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        LABEL_SS = "color: #007c91; font-weight: bold; font-size: 13px;"
        VALUE_SS   = "color: #212121; font-size: 13px;"

        if articolo:
            # Articolo trovato — mostra in sola lettura con contrasto elevato
            grp = QGroupBox("Articolo trovato in anagrafica")
            grp.setStyleSheet(
                "QGroupBox { color: #80cbc4; font-weight: bold; border: 1px solid #37474f;"
                " padding: 10px; margin-top: 8px; }"
                "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }")
            form = QFormLayout(grp)
            form.setSpacing(10)
            for label, value in [
                ("Codice:",        articolo.codice or "—"),
                ("Descrizione:",   articolo.descrizione or "—"),
                ("UM:",            articolo.um or "—"),
                ("Prezzo listino:", f"€ {articolo.prezzo:.4f}" if articolo.prezzo else "—"),
                ("Peso lordo:",    f"{articolo.peso_lordo} kg" if articolo.peso_lordo else "—"),
                ("Peso netto:",    f"{articolo.peso_netto} kg" if articolo.peso_netto else "—"),
            ]:
                k = QLabel(label);  k.setStyleSheet(LABEL_SS)
                v = QLabel(value);  v.setStyleSheet(VALUE_SS)
                form.addRow(k, v)
            self.ana_layout.addWidget(grp)
            self.ana_layout.addStretch()
        else:
            # Articolo non presente — form di creazione con campi editabili
            warn = QLabel(f"⚠  Codice <b>{self.codice}</b> non trovato nell'anagrafica Articoli.")
            warn.setStyleSheet("color: #ffb74d; font-size: 13px; margin: 10px;")
            warn.setTextFormat(Qt.RichText)
            self.ana_layout.addWidget(warn)

            grp = QGroupBox("Crea in Anagrafica")
            grp.setStyleSheet(
                "QGroupBox { color: #aaa; font-weight: bold; border: 1px solid #444;"
                " padding: 10px; margin-top: 8px; }"
                "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }")
            form = QFormLayout(grp)
            form.setSpacing(8)

            self._ed_codice = QLineEdit(self.codice)
            self._ed_descr  = QLineEdit(self.descrizione)
            pu = self.riga_data.get('prezzo_unitario', 0.0) or 0.0
            self._ed_prezzo = QLineEdit(f"{pu:.4f}")

            # UM obbligatorio — dropdown
            self._cb_um = QComboBox()
            self._cb_um.addItems(self._UM_OPTIONS)
            self._cb_um.setStyleSheet(
                "QComboBox { background: #263238; color: #e0e0e0; padding: 2px 6px; }"
                "QComboBox::drop-down { border: none; }")

            for lbl_txt, widget in [
                ("Codice:", self._ed_codice),
                ("Descrizione:", self._ed_descr),
                ("UM *:", self._cb_um),
                ("Prezzo:", self._ed_prezzo),
            ]:
                lk = QLabel(lbl_txt); lk.setStyleSheet(LABEL_SS)
                form.addRow(lk, widget)

            note = QLabel("* Campo obbligatorio")
            note.setStyleSheet("color: #ef9a9a; font-size: 11px; margin-top: 2px;")
            form.addRow("", note)

            btn_crea = QPushButton("➕ Crea in Anagrafica")
            btn_crea.setStyleSheet(
                "background-color: #388e3c; color: white; font-weight: bold; "
                "height: 34px; border-radius: 4px;")
            btn_crea.clicked.connect(self._create_article)
            form.addRow("", btn_crea)

            self.ana_layout.addWidget(grp)
            self.ana_layout.addStretch()

    def _create_article(self):
        if not self.main_win: return
        codice = self._ed_codice.text().strip()
        um     = self._cb_um.currentText().strip()
        if not codice:
            QMessageBox.warning(self, "Errore", "Il codice articolo è obbligatorio.")
            return
        if not um:
            QMessageBox.warning(self, "UM obbligatorio",
                "Seleziona l'Unità di Misura prima di salvare l'articolo.")
            self._cb_um.setFocus()
            return
        session = self.main_win.db_manager.get_session()
        try:
            existing = session.query(Articolo).filter_by(codice=codice).first()
            if existing:
                QMessageBox.warning(self, "Già presente",
                    f"Il codice '{codice}' esiste già in anagrafica.")
                return
            try:
                prezzo = float(self._ed_prezzo.text().replace(',', '.'))
            except ValueError:
                prezzo = 0.0
            art = Articolo(
                codice=codice,
                descrizione=self._ed_descr.text().strip(),
                um=um,
                prezzo=prezzo,
            )
            session.add(art)
            session.commit()
            QMessageBox.information(self, "Creato",
                f"Articolo '{codice}' ({um}) creato in anagrafica.")
            self._populate_anagrafica(art)
            self.tabs.setTabText(2, "📦 Anagrafica")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Errore", str(e))
        finally:
            session.close()


class InvoiceDetailDialog(QDialog):
    """Summary dialog for an invoice."""
    DETAIL_HEADERS = ["UM", "Codice", "Descrizione", "Quantità", "Prezzo Unit.", "Totale Riga", "🔍"]
    PREFS_KEY = "invoice_detail_widths"

    def __init__(self, fattura_or_id, parent=None):
        super().__init__(parent)
        self.main_win = parent
        while self.main_win and not hasattr(self.main_win, 'db_manager'):
            self.main_win = self.main_win.parent()

        # Handle both object and ID for flexibility
        if isinstance(fattura_or_id, int):
            self.fattura_id = fattura_or_id
            self.fattura = None
        else:
            self.fattura = fattura_or_id
            self.fattura_id = fattura_or_id.id

        self.setWindowTitle(f"Fattura n. ... Caricamento...")
        self.resize(900, 600)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header Details
        self.info_group = QGroupBox("Dati Fattura")
        self.info_layout = QFormLayout(self.info_group)
        self.lbl_num = QLabel("-")
        self.lbl_data = QLabel("-")
        self.lbl_cli = QLabel("-")
        self.lbl_caus = QLabel("-")
        
        self.info_layout.addRow("Numero:", self.lbl_num)
        self.info_layout.addRow("Data:", self.lbl_data)
        
        # Dynamic label for Cliente/Fornitore
        self.lbl_cli_forn_tag = QLabel("Cliente/Fornitore:")
        self.info_layout.addRow(self.lbl_cli_forn_tag, self.lbl_cli)
        self.info_layout.addRow("Causale:", self.lbl_caus)
        
        layout.addWidget(self.info_group)

        # Rows Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.DETAIL_HEADERS))
        self.table.setHorizontalHeaderLabels(self.DETAIL_HEADERS)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().sectionMoved.connect(lambda: save_column_order(self.table, "invoice_detail"))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)
        restore_column_order(self.table, "invoice_detail")

        # Footer Total
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        self.lbl_tot = QLabel("TOTALE FATTURA: € 0.00")
        self.lbl_tot.setStyleSheet("font-size: 18px; font-weight: bold; color: #00bcd4;")
        footer_layout.addWidget(self.lbl_tot)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_jump = QPushButton("👤 Vedi Dettaglio")
        self.btn_jump.clicked.connect(self.jump_to_entity)
        btn_layout.addWidget(self.btn_jump)
        btn_layout.addStretch()
        
        layout.addLayout(footer_layout)
        layout.addLayout(btn_layout)

    def load_data(self):
        """Fetch fresh data in a new session to avoid DetachedInstanceError."""
        if not self.main_win: return
        
        session = self.main_win.db_manager.get_session()
        try:
            # Eager load righe and their articoli for efficiency and safety
            self.fattura = session.get(Fattura, self.fattura_id, options=[
                joinedload(Fattura.righe).joinedload(RigaFattura.articolo)
            ])
            
            if self.fattura:
                self.setWindowTitle(f"Fattura n. {self.fattura.numero} del {self.fattura.data}")
                self.lbl_num.setText(str(self.fattura.numero))
                self.lbl_data.setText(str(self.fattura.data))
                
                if self.fattura.tipo == 'ACQUISTO':
                    self.lbl_cli_forn_tag.setText("Fornitore:")
                    self.lbl_cli.setText(self.fattura.fornitore_denominazione or self.fattura.fornitore_codice or "-")
                    self.btn_jump.setText("📦 Vedi Fornitore")
                else:
                    self.lbl_cli_forn_tag.setText("Cliente:")
                    self.lbl_cli.setText(self.fattura.cliente_denominazione or self.fattura.cliente_codice or "-")
                    self.btn_jump.setText("👤 Vedi Cliente")
                    
                self.lbl_caus.setText(self.fattura.causale or "-")
                self.lbl_tot.setText(f"TOTALE FATTURA: € {self.fattura.totale:.2f}")
                
                self.load_rows()
                self._restore_column_widths()
        except Exception as e:
            print(f"Error loading invoice detail: {e}")
        finally:
            session.close()

    def jump_to_entity(self):
        # Pass both code and denomination for robust search
        if self.main_win and self.fattura:
            if self.fattura.tipo == 'ACQUISTO':
                self.main_win.open_supplier_by_code(
                    self.fattura.fornitore_codice, 
                    self.fattura.fornitore_denominazione
                )
            else:
                self.main_win.open_client_by_code(
                    self.fattura.cliente_codice, 
                    self.fattura.cliente_denominazione
                )

    def load_rows(self):
        if not self.fattura: return
        righe = self.fattura.righe
        self.table.setRowCount(len(righe))
        self.table.setSortingEnabled(False)  # disabilita durante il riempimento (necessario per setCellWidget)
        for i, r in enumerate(righe):
            # UM
            um_val = ""
            if r.articolo and r.articolo.um:
                um_val = r.articolo.um
            self.table.setItem(i, 0, QTableWidgetItem(um_val))
            self.table.setItem(i, 1, QTableWidgetItem(r.articolo_codice or ""))
            self.table.setItem(i, 2, QTableWidgetItem(r.descrizione or ""))
            self.table.setItem(i, 3, QTableWidgetItem(f"{r.quantita:.2f}" if r.quantita else "0.00"))
            self.table.setItem(i, 4, QTableWidgetItem(f"€ {r.prezzo_unitario:.2f}" if r.prezzo_unitario else "€ 0.00"))
            self.table.setItem(i, 5, QTableWidgetItem(f"€ {r.totale_riga:.2f}" if r.totale_riga else "€ 0.00"))

            # Pulsante cross-reference
            btn_xref = QPushButton("🔍")
            btn_xref.setFixedSize(28, 24)
            btn_xref.setStyleSheet(
                "QPushButton { background-color: #37474f; color: #80cbc4; border-radius: 3px; font-size: 11px; }"
                "QPushButton:hover { background-color: #00bcd4; color: white; }"
                "QPushButton:disabled { color: #555; background-color: #2a2a2a; }")
            btn_xref.setToolTip(f"Cross-reference: {r.articolo_codice or 'nessun codice'}" )
            if r.articolo_codice:
                riga_data = {
                    'prezzo_unitario': r.prezzo_unitario,
                    'quantita': r.quantita,
                    'totale_riga': r.totale_riga,
                }
                codice_snap = r.articolo_codice
                descr_snap  = r.descrizione or ""
                btn_xref.clicked.connect(
                    lambda checked=False, cod=codice_snap, des=descr_snap, rd=riga_data:
                    CrossReferenceDialog(cod, des, rd, self).exec()
                )
            else:
                btn_xref.setEnabled(False)
            self.table.setCellWidget(i, 6, btn_xref)

        self.table.setSortingEnabled(True)

    def _restore_column_widths(self):
        """Restore saved column widths from preferences."""
        prefs = load_column_prefs()
        widths = prefs.get(self.PREFS_KEY)
        if widths and len(widths) == self.table.columnCount():
            for i, w in enumerate(widths):
                self.table.setColumnWidth(i, w)
        else:
            # Default widths: UM, Codice, Descrizione, Qtà, Prezzo, Totale, 🔍
            defaults = [50, 120, 260, 70, 100, 90, 36]
            for i, w in enumerate(defaults[:self.table.columnCount()]):
                self.table.setColumnWidth(i, w)

    def _save_column_widths(self):
        """Save current column widths to preferences."""
        prefs = load_column_prefs()
        widths = [self.table.columnWidth(i) for i in range(self.table.columnCount())]
        prefs[self.PREFS_KEY] = widths
        save_column_prefs(prefs)

    def closeEvent(self, event):
        """Save column widths when dialog is closed and notify parent."""
        self._save_column_widths()
        if hasattr(self, 'window_id'):
            main_win = self.parent()
            while main_win and not hasattr(main_win, 'remove_detail_window'):
                main_win = main_win.parent()
            if main_win:
                main_win.remove_detail_window(self.window_id)
        super().closeEvent(event)


def get_icon(name):
    """Returns a QIcon from an SVG string for consistent rendering."""
    svgs = {
        "email": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00bcd4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>""",
        "web": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00bcd4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>""",
        "map": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00bcd4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>"""
    }
    if name not in svgs: return QIcon()
    
    # Render SVG to pixmap
    from PySide6.QtGui import QPixmap, QPainter
    from PySide6.QtSvg import QSvgRenderer
    
    renderer = QSvgRenderer(svgs[name].encode('utf-8'))
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    return QIcon(pixmap)


class MailSelectorDialog(QDialog):
    """Dialog to choose how to send an email, detecting installed apps."""
    def __init__(self, email, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Invia Email")
        self.email = email
        self.setFixedWidth(450)
        self.setMinimumHeight(600)
        self.setup_ui()

    def get_installed_mail_apps(self):
        """Scans Windows registry for installed mail clients."""
        apps = []
        try:
            key_path = r"SOFTWARE\Clients\Mail"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            # Try to get the friendly name or use the key name
                            try:
                                app_name = winreg.QueryValue(subkey, None)
                            except:
                                app_name = subkey_name
                            
                            # Get the command to open
                            try:
                                cmd_path = r"shell\open\command"
                                with winreg.OpenKey(subkey, cmd_path) as cmd_key:
                                    command = winreg.QueryValue(cmd_key, None)
                                    if command:
                                        # Clean up command (remove quotes, etc.)
                                        command = command.split('"')[1] if '"' in command else command.split(' ')[0]
                                        if os.path.exists(command):
                                            apps.append((app_name, command))
                            except:
                                continue
                    except:
                        continue
        except Exception as e:
            print(f"Errore scansione registro: {e}")
        return apps

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        info = QLabel(f"Seleziona un'applicazione per inviare l'email a:<br><b style='color: #00bcd4; font-size: 16px;'>{self.email}</b>")
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        info.setStyleSheet("""
            QLabel {
                font-size: 14px; 
                margin-bottom: 5px; 
                padding: 15px; 
                background: #252525; 
                border: 1px solid #333;
                border-radius: 8px;
                color: #e0e0e0;
            }
        """)
        layout.addWidget(info)
        
        # 1. Local Apps
        label_local = QLabel("APPLICAZIONI INSTALLATE")
        label_local.setStyleSheet("color: #00bcd4; font-size: 12px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(label_local)
        
        local_apps = self.get_installed_mail_apps()
        
        # Fallback for Thunderbird if not in registry but in path (common)
        tb_paths = [
            r"C:\Program Files\Mozilla Thunderbird\thunderbird.exe",
            r"C:\Program Files (x86)\Mozilla Thunderbird\thunderbird.exe"
        ]
        for path in tb_paths:
            if os.path.exists(path) and not any(path in a[1] for a in local_apps):
                local_apps.append(("Mozilla Thunderbird", path))

        if not any("mailto" in str(a[1]) for a in local_apps):
            local_apps.insert(0, ("Predefinita di Sistema", "mailto"))

        for name, path in local_apps:
            icon = "📧"
            if "thunderbird" in path.lower(): icon = "🕊️"
            elif "outlook" in path.lower(): icon = "✉️"
            
            btn = self.create_option_button(f"{icon}  {name}", path)
            layout.addWidget(btn)

        # 2. Webmail
        label_web = QLabel("WEBMAIL")
        label_web.setStyleSheet("color: #00bcd4; font-size: 12px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(label_web)
        
        web_options = [
            ("Gmail", "🌐 G", f"https://mail.google.com/mail/?view=cm&fs=1&to={self.email}"),
            ("Outlook / Hotmail", "🌐 O", f"https://outlook.office.com/mail/deeplink/compose?to={self.email}")
        ]
        
        for name, icon, url in web_options:
            btn = self.create_option_button(f"{icon}  {name}", url)
            layout.addWidget(btn)
            
        # 3. Utilities
        label_util = QLabel("ALTRO")
        label_util.setStyleSheet("color: #00bcd4; font-size: 12px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(label_util)
        
        btn_copy = self.create_option_button("📋  Copia Indirizzo Email", "copy")
        layout.addWidget(btn_copy)
        
        layout.addSpacing(10)
        btn_cancel = QPushButton("Annulla")
        btn_cancel.setFixedHeight(45)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #444;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #444;
                border-color: #555;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

    def create_option_button(self, text, action):
        btn = QPushButton(text)
        btn.setFixedHeight(50)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 20px;
                font-size: 15px;
                border: 1px solid #333;
                border-radius: 8px;
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #2e2e2e;
                border-color: #00bcd4;
                color: #00bcd4;
            }
        """)
        btn.clicked.connect(lambda _, a=action: self.handle_action(a))
        return btn

    def handle_action(self, action):
        if action == "copy":
            QApplication.clipboard().setText(self.email)
            QMessageBox.information(self, "Copiato", "Indirizzo email copiato negli appunti.")
        elif action == "mailto":
            QDesktopServices.openUrl(QUrl(f"mailto:{self.email}"))
        elif action.startswith("http"):
            QDesktopServices.openUrl(QUrl(action))
        else:
            # Assume it's an executable path
            try:
                if "thunderbird.exe" in action.lower():
                    subprocess.Popen([action, "-compose", f"to={self.email}"])
                else:
                    # Generic launch (might need mailto if it's not and exe)
                    if os.path.exists(action):
                        # Try passing mailto to the exe as argument? 
                        # Most mail apps support mailto:email
                        subprocess.Popen([action, f"mailto:{self.email}"])
                    else:
                        QDesktopServices.openUrl(QUrl(f"mailto:{self.email}"))
            except Exception as e:
                QMessageBox.warning(self, "Errore", f"Impossibile avviare l'applicazione: {e}")
        self.accept()


class ClientInvoicesDialog(QDialog):
    """Dialog to show all invoices of a specific client."""
    def __init__(self, cliente, invoices, parent=None):
        super().__init__(parent)
        name = cliente.ragione_sociale if cliente else "Sconosciuto"
        self.setWindowTitle(f"Fatture Cliente: {name}")
        self.resize(1000, 550)
        self.invoices = invoices
        
        # Calculate totals
        self.total_amount = sum(inv.totale for inv in invoices)
        self.total_count = len(invoices)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel(f"Elenco Fatture")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #00bcd4;")
        layout.addWidget(header)
        
        self.table = QTableWidget()
        headers = ["Numero", "Data", "Causale", "Totale", "Azioni"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().sectionMoved.connect(lambda: save_column_order(self.table, "client_invoices"))
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        restore_column_order(self.table, "client_invoices")
        
        self.table.setRowCount(len(self.invoices))
        for i, inv in enumerate(self.invoices):
            self.table.setItem(i, 0, make_item(inv.numero))
            self.table.setItem(i, 1, make_item(inv.data))
            self.table.setItem(i, 2, make_item(inv.causale or ""))
            self.table.setItem(i, 3, make_item(f"€ {inv.totale:.2f}", raw_value=inv.totale))
            
            # Action button or text
            act_item = QTableWidgetItem("🔍 Dettaglio")
            act_item.setForeground(QColor("#00bcd4"))
            self.table.setItem(i, 4, act_item)
            
            # Store ID in UserRole for the erste column
            self.table.item(i, 0).setData(Qt.UserRole, inv.id)

        self.table.cellDoubleClicked.connect(self.open_detail)
        self.table.cellClicked.connect(self.handle_click)
        layout.addWidget(self.table)
        
        # Footer with totals
        footer = QFrame()
        footer.setObjectName("footer_totals")
        footer.setFrameShape(QFrame.StyledPanel)
        footer_layout = QHBoxLayout(footer)
        
        label_count = QLabel(f"Numero Fatture: {self.total_count}")
        label_count.setStyleSheet("font-weight: bold;")
        
        label_total = QLabel(f"Importo Totale: € {self.total_amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        label_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #00bcd4;")
        
        footer_layout.addWidget(label_count)
        footer_layout.addStretch()
        footer_layout.addWidget(label_total)
        layout.addWidget(footer)

        btn_close = QPushButton("Chiudi")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def open_detail(self, row, col):
        inv_id = self.table.item(row, 0).data(Qt.UserRole)
        if inv_id:
            main_win = self.parent()
            while main_win and not hasattr(main_win, 'db_manager'):
                main_win = main_win.parent()
            
            if main_win:
                session = main_win.db_manager.get_session()
                fattura = session.get(Fattura, inv_id)
                if fattura:
                    main_win.show_detail_window(f"invoice_{inv_id}", InvoiceDetailDialog, fattura)
                session.close()

    def handle_click(self, row, col):
        if self.table.horizontalHeaderItem(col).text() == "Azioni":
            self.open_detail(row, col)

    def closeEvent(self, event):
        if hasattr(self, 'window_id'):
            main_win = self.parent()
            while main_win and not hasattr(main_win, 'remove_detail_window'):
                main_win = main_win.parent()
            if main_win:
                main_win.remove_detail_window(self.window_id)
        super().closeEvent(event)


class ClientDetailDialog(QDialog):
    """Dialog to show all details of a client."""
    def __init__(self, cliente, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Dettagli Cliente: {cliente.ragione_sociale}")
        self.resize(800, 600)
        self.cliente = cliente
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Grouping fields
        groups = [
            ("Dati Generali", [
                ("Codice", self.cliente.codice),
                ("Codice Alternativo", self.cliente.codice_alternativo),
                ("Ragione Sociale", self.cliente.ragione_sociale),
                ("Partita IVA", self.cliente.partita_iva),
                ("Codice Fiscale", self.cliente.codice_fiscale)
            ]),
            ("Indirizzo", [
                ("Indirizzo", self.cliente.indirizzo),
                ("CAP", self.cliente.cap),
                ("Località", self.cliente.localita),
                ("Provincia", self.cliente.provincia),
                ("Nazione", self.cliente.nazione)
            ]),
            ("Contatti", [
                ("Telefono", self.cliente.telefono),
                ("Telefono 2", self.cliente.telefono2),
                ("Cellulare", self.cliente.cellulare),
                ("E-mail", self.cliente.email),
                ("Sito Web", self.cliente.internet)
            ]),
            ("Pagamento", [
                ("Codice Pagamento", self.cliente.pagamento),
                ("Descrizione Pagamento", self.cliente.descrizione_pagamento),
                ("Banca", self.cliente.banca),
                ("Filiale", self.cliente.filiale),
                ("ABI", self.cliente.abi),
                ("CIN", self.cliente.cin),
                ("Conto Corrente", self.cliente.conto_corrente),
                ("IBAN", self.cliente.iban),
                ("BIC", self.cliente.bic)
            ]),
            ("Altro", [
                ("Agente", self.cliente.agente),
                ("Listino", self.cliente.listino),
                ("Zona", self.cliente.zona),
                ("Area", self.cliente.area),
                ("Categoria", self.cliente.categoria),
                ("Statistico", self.cliente.statistico),
                ("Riferimento", self.cliente.riferimento),
                ("Commento", self.cliente.commento)
            ])
        ]
        
        for title, fields in groups:
            group_box = QGroupBox(title)
            form = QFormLayout(group_box)
            for label, value in fields:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(10)
                
                val_label = QLabel(str(value) if value else "-")
                val_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                val_label.setStyleSheet("font-size: 14px;")
                row_layout.addWidget(val_label)
                
                # Action Buttons
                # Map labels to their actions
                if value and value != "-":
                    btn = QPushButton() # Create button here to avoid repetition
                    if label == "E-mail":
                        btn.setIcon(get_icon("email"))
                        btn.setToolTip(f"Invia email a {value}")
                        btn.clicked.connect(lambda _, v=value: MailSelectorDialog(v, self).exec())
                        self._setup_action_button(btn, row_layout)
                    elif label == "Sito Web":
                        btn.setIcon(get_icon("web"))
                        btn.setToolTip(f"Visita {value}")
                        url = value if value.startswith("http") else f"http://{value}"
                        btn.clicked.connect(lambda _, u=url: QDesktopServices.openUrl(QUrl(u)))
                        self._setup_action_button(btn, row_layout)
                    elif label == "Indirizzo":
                        btn.setIcon(get_icon("map"))
                        btn.setToolTip("Apri in Google Maps")
                        full_addr = f"{value}, {self.cliente.cap} {self.cliente.localita} {self.cliente.provincia}"
                        btn.clicked.connect(lambda _, q=full_addr: QDesktopServices.openUrl(QUrl(f"https://www.google.com/maps/search/?api=1&query={q}")))
                        self._setup_action_button(btn, row_layout)
                
                row_layout.addStretch()
                form.addRow(f"<b>{label}:</b>", row_widget)
            content_layout.addWidget(group_box)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Action Buttons Bottom
        btn_layout = QHBoxLayout()
        btn_inv = QPushButton("🔍 Vedi Fatture")
        btn_inv.clicked.connect(self.jump_to_invoices)
        btn_layout.addWidget(btn_inv)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)

    def closeEvent(self, event):
        if hasattr(self, 'window_id'):
            main_win = self.parent()
            while main_win and not hasattr(main_win, 'remove_detail_window'):
                main_win = main_win.parent()
            if main_win:
                main_win.remove_detail_window(self.window_id)
        super().closeEvent(event)

    def _setup_action_button(self, btn, layout):
        btn.setFixedSize(30, 30)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { 
                border: 1px solid #00bcd4; 
                border-radius: 15px; 
                background: transparent; 
                color: #00bcd4;
                font-size: 14px;
                font-weight: bold;
            } 
            QPushButton:hover { 
                background-color: #00bcd4; 
                color: white;
            }
        """)
        layout.addWidget(btn)

    def jump_to_invoices(self):
        main_win = self.parent()
        while main_win and not hasattr(main_win, 'open_invoices_by_client'):
            main_win = main_win.parent()
        
        if main_win:
            # Pass both code and name for robust search
            main_win.open_invoices_by_client(self.cliente.codice, self.cliente.ragione_sociale)


class SupplierDetailDialog(QDialog):
    """Dialog to show all details of a supplier."""
    def __init__(self, fornitore, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Dettagli Fornitore: {fornitore.ragione_sociale}")
        self.resize(800, 600)
        self.fornitore = fornitore
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Grouping fields
        groups = [
            ("Dati Generali", [
                ("Codice", self.fornitore.codice),
                ("Ragione Sociale", self.fornitore.ragione_sociale),
                ("Codice Fiscale", self.fornitore.codice_fiscale),
                ("Partita IVA", self.fornitore.partita_iva),
                ("IVA Intra", self.fornitore.partita_iva_intra)
            ]),
            ("Indirizzo", [
                ("Indirizzo Esteso", self.fornitore.indirizzo_esteso),
                ("Indirizzo", self.fornitore.indirizzo),
                ("CAP", self.fornitore.cap),
                ("Località", self.fornitore.localita),
                ("Provincia", self.fornitore.provincia),
                ("Nazione", self.fornitore.nazione)
            ]),
            ("Contatti", [
                ("Telefono", self.fornitore.telefono),
                ("Fax", self.fornitore.fax),
                ("E-mail", self.fornitore.email)
            ]),
            ("Pagamento", [
                ("Codice Pagamento", self.fornitore.pagamento),
                ("Descrizione Pagamento", self.fornitore.descrizione_pagamento),
                ("Banca", self.fornitore.banca),
                ("Filiale", self.fornitore.filiale),
                ("ABI", self.fornitore.abi),
                ("CAB", self.fornitore.cab),
                ("Conto Corrente", self.fornitore.conto_corrente),
                ("IBAN", self.fornitore.iban)
            ]),
            ("Altro", [
                ("Porto", self.fornitore.porto),
                ("Spedizione", self.fornitore.spedizione)
            ])
        ]
        
        for title, fields in groups:
            group_box = QGroupBox(title)
            form = QFormLayout(group_box)
            for label, value in fields:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(10)
                
                val_label = QLabel(str(value) if value else "-")
                val_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                val_label.setStyleSheet("font-size: 14px;")
                row_layout.addWidget(val_label)
                
                # Action Buttons
                if value and value != "-":
                    btn = QPushButton() # Create button here to avoid repetition
                    if label == "E-mail":
                        btn.setIcon(get_icon("email"))
                        btn.setToolTip(f"Invia email a {value}")
                        btn.clicked.connect(lambda _, v=value: MailSelectorDialog(v, self).exec())
                        self._setup_action_button(btn, row_layout)
                    elif label == "Indirizzo":
                        btn.setIcon(get_icon("map"))
                        btn.setToolTip("Apri in Google Maps")
                        full_addr = f"{value}, {self.fornitore.cap} {self.fornitore.localita} {self.fornitore.provincia}"
                        btn.clicked.connect(lambda _, q=full_addr: QDesktopServices.openUrl(QUrl(f"https://www.google.com/maps/search/?api=1&query={q}")))
                        self._setup_action_button(btn, row_layout)
                
                row_layout.addStretch()
                form.addRow(f"<b>{label}:</b>", row_widget)
            content_layout.addWidget(group_box)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        btn_close = QPushButton("Chiudi")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _setup_action_button(self, btn, layout):
        btn.setFixedSize(30, 30)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { 
                border: 1px solid #00bcd4; 
                border-radius: 15px; 
                background: transparent; 
                color: #00bcd4;
                font-size: 14px;
                font-weight: bold;
            } 
            QPushButton:hover { 
                background-color: #00bcd4; 
                color: white;
            }
        """)
        layout.addWidget(btn)

    def closeEvent(self, event):
        if hasattr(self, 'window_id'):
            main_win = self.parent()
            while main_win and not hasattr(main_win, 'remove_detail_window'):
                main_win = main_win.parent()
            if main_win:
                main_win.remove_detail_window(self.window_id)
        super().closeEvent(event)


class ArticleDetailDialog(QDialog):
    """Dialog a 3 tab per la scheda articolo: dati, storico acquisti, storico vendite."""

    _UM_OPTIONS = ["", "nr", "mt", "kg", "lt", "conf"]

    def __init__(self, articolo, parent=None):
        super().__init__(parent)
        self.articolo = articolo
        self.main_win = parent
        while self.main_win and not hasattr(self.main_win, 'db_manager'):
            self.main_win = self.main_win.parent()
        self.setWindowTitle(f"Articolo: {articolo.codice}")
        self.resize(820, 540)
        self.setup_ui()
        self.load_storico()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Intestazione
        hdr = QLabel(f"<b>{self.articolo.codice}</b>  —  {self.articolo.descrizione or ''}")
        hdr.setStyleSheet("font-size: 15px; color: #00bcd4; margin: 6px;")
        hdr.setTextFormat(Qt.RichText)
        layout.addWidget(hdr)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ── Tab Dati Articolo ──
        tab_dati = QWidget()
        dati_layout = QVBoxLayout(tab_dati)

        LABEL_SS = "color: #212121; font-size: 13px;"
        KEY_SS   = "color: #00695c; font-weight: bold; font-size: 13px;"

        gen_group = QGroupBox("Dati Generali")
        gen_group.setStyleSheet("QGroupBox { color: #aaa; font-weight: bold; border: 1px solid #444; padding: 8px; }")
        gen_layout = QFormLayout(gen_group)
        gen_layout.setSpacing(8)

        def _lbl(text):
            l = QLabel(text or "—")
            l.setStyleSheet(LABEL_SS)
            return l
        def _key(text):
            l = QLabel(text)
            l.setStyleSheet(KEY_SS)
            return l

        gen_layout.addRow(_key("Codice:"),       _lbl(self.articolo.codice))
        gen_layout.addRow(_key("Descrizione:"),  _lbl(self.articolo.descrizione))
        gen_layout.addRow(_key("UM:"),           _lbl(self.articolo.um))
        prezzo_str = f"€ {self.articolo.prezzo:.4f}" if self.articolo.prezzo else "—"
        gen_layout.addRow(_key("Prezzo listino:"), _lbl(prezzo_str))
        dati_layout.addWidget(gen_group)

        log_group = QGroupBox("Logistica e Pesi")
        log_group.setStyleSheet("QGroupBox { color: #aaa; font-weight: bold; border: 1px solid #444; padding: 8px; }")
        log_layout = QFormLayout(log_group)
        log_layout.setSpacing(8)
        log_layout.addRow(_key("Peso Lordo (kg):"), _lbl(str(self.articolo.peso_lordo) if self.articolo.peso_lordo else "—"))
        log_layout.addRow(_key("Peso Netto (kg):"), _lbl(str(self.articolo.peso_netto) if self.articolo.peso_netto else "—"))
        dati_layout.addWidget(log_group)
        dati_layout.addStretch()
        self.tabs.addTab(tab_dati, "📋 Dati")

        # ── Tab Storico Acquisti ──
        tab_acq = QWidget()
        acq_lay = QVBoxLayout(tab_acq)
        self.tbl_acq = QTableWidget()
        self.tbl_acq.setColumnCount(5)
        self.tbl_acq.setHorizontalHeaderLabels(["Data", "Fornitore", "N° Fatt.", "Qtà", "Prezzo Acq."])
        self.tbl_acq.horizontalHeader().setStretchLastSection(True)
        self.tbl_acq.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_acq.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_acq.setSortingEnabled(True)
        acq_lay.addWidget(self.tbl_acq)
        self.lbl_acq = QLabel()
        self.lbl_acq.setStyleSheet("color: #aaa; font-size: 12px;")
        acq_lay.addWidget(self.lbl_acq)
        self.tabs.addTab(tab_acq, "🛒 Acquisti")

        # ── Tab Storico Vendite ──
        tab_vend = QWidget()
        vend_lay = QVBoxLayout(tab_vend)
        self.tbl_vend = QTableWidget()
        self.tbl_vend.setColumnCount(5)
        self.tbl_vend.setHorizontalHeaderLabels(["Data", "Cliente", "N° Fatt.", "Qtà", "Prezzo Vend."])
        self.tbl_vend.horizontalHeader().setStretchLastSection(True)
        self.tbl_vend.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_vend.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_vend.setSortingEnabled(True)
        vend_lay.addWidget(self.tbl_vend)
        self.lbl_vend = QLabel()
        self.lbl_vend.setStyleSheet("color: #aaa; font-size: 12px;")
        vend_lay.addWidget(self.lbl_vend)
        self.tabs.addTab(tab_vend, "💰 Vendite")

        # Chiudi
        btn_close = QPushButton("Chiudi")
        btn_close.clicked.connect(self.accept)
        btn_close.setFixedHeight(30)
        btn_close.setStyleSheet("background-color: #444; color: #ccc; padding: 0 20px; border-radius: 4px;")
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

    def load_storico(self):
        if not self.main_win: return
        codice = self.articolo.codice
        session = self.main_win.db_manager.get_session()
        try:
            from sqlalchemy.orm import joinedload
            acquisti = (session.query(RigaFattura)
                .join(Fattura)
                .filter(Fattura.tipo == 'ACQUISTO', RigaFattura.articolo_codice == codice)
                .options(joinedload(RigaFattura.fattura))
                .order_by(Fattura.data.desc()).all())
            vendite  = (session.query(RigaFattura)
                .join(Fattura)
                .filter(Fattura.tipo == 'VENDITA',  RigaFattura.articolo_codice == codice)
                .options(joinedload(RigaFattura.fattura))
                .order_by(Fattura.data.desc()).all())

            self._fill_table(self.tbl_acq, acquisti, tipo='acq')
            self._fill_table(self.tbl_vend, vendite,  tipo='vend')

            tot_acq  = sum((r.totale_riga or 0) for r in acquisti)
            tot_vend = sum((r.totale_riga or 0) for r in vendite)
            self.lbl_acq.setText(f"Totale: {len(acquisti)} righe — € {tot_acq:.2f}")
            self.lbl_vend.setText(f"Totale: {len(vendite)} righe — € {tot_vend:.2f}")

            self.tabs.setTabText(1, f"🛒 Acquisti ({len(acquisti)})")
            self.tabs.setTabText(2, f"💰 Vendite ({len(vendite)})")
        except Exception as e:
            print(f"Errore storico articolo: {e}")
        finally:
            session.close()

    def _fill_table(self, tbl, righe, tipo):
        tbl.setRowCount(len(righe))
        for i, r in enumerate(righe):
            ft = r.fattura
            tbl.setItem(i, 0, QTableWidgetItem(str(ft.data) if ft.data else "—"))
            entity = (ft.fornitore_denominazione or ft.fornitore_codice) if tipo == 'acq' else (ft.cliente_denominazione or ft.cliente_codice)
            tbl.setItem(i, 1, QTableWidgetItem(entity or "—"))
            tbl.setItem(i, 2, QTableWidgetItem(str(ft.numero) if ft.numero else "—"))
            tbl.setItem(i, 3, QTableWidgetItem(f"{r.quantita:.2f}" if r.quantita else "0.00"))
            tbl.setItem(i, 4, QTableWidgetItem(f"€ {r.prezzo_unitario:.4f}" if r.prezzo_unitario else "€ 0.00"))

    def closeEvent(self, event):
        if hasattr(self, 'window_id'):
            main_win = self.parent()
            while main_win and not hasattr(main_win, 'remove_detail_window'):
                main_win = main_win.parent()
            if main_win:
                main_win.remove_detail_window(self.window_id)
        super().closeEvent(event)


class ArticleSearchDialog(QDialog):
    """Dialog for searching items across all invoice lines."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ricerca Articolo nelle Fatture")
        self.setMinimumSize(1100, 700)
        self.active_search_steps = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Search input
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cerca articoli (es: %mixer %statico %blu)...")
        self.search_input.setFixedHeight(45)
        self.search_input.setStyleSheet("font-size: 16px; padding-left: 10px; border: 1px solid #00bcd4; border-radius: 5px;")
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        
        btn_search = QPushButton("CERCA")
        btn_search.setFixedHeight(45)
        btn_search.setFixedWidth(120)
        btn_search.setCursor(Qt.PointingHandCursor)
        btn_search.setStyleSheet("""
            QPushButton {
                background-color: #00bcd4;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #00acc1;
            }
        """)
        btn_search.clicked.connect(self.perform_search)
        search_layout.addWidget(btn_search)
        layout.addLayout(search_layout)
        
        # Search field options
        options_layout = QHBoxLayout()
        self.cb_code = QCheckBox("Codice articolo")
        self.cb_desc = QCheckBox("Descrizione articolo")
        self.cb_code.setChecked(True)
        self.cb_desc.setChecked(True)
        self.cb_code.setStyleSheet("font-weight: bold; color: #00bcd4;")
        self.cb_desc.setStyleSheet("font-weight: bold; color: #00bcd4;")
        options_layout.addWidget(self.cb_code)
        options_layout.addWidget(self.cb_desc)
        
        # Incremental search option
        self.cb_incremental = QCheckBox("Ricerca incrementale")
        self.cb_incremental.setStyleSheet("font-weight: bold; color: #ffb74d;")
        self.cb_incremental.setToolTip("Se attivo, la ricerca corrente filtra i risultati precedenti.")
        self.cb_incremental.stateChanged.connect(self.update_search_mode_label)
        options_layout.addWidget(self.cb_incremental)
        
        self.lbl_mode = QLabel("Modalità: Nuova ricerca")
        self.lbl_mode.setStyleSheet("color: #888; font-weight: bold; margin-left: 10px;")
        options_layout.addWidget(self.lbl_mode)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Fattura", "Data", "Cliente", "Cod. Cli", "Cod. Art.",
            "Descrizione Articolo", "Q.tà", "Prezzo", "Totale", "Azioni"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        header.setSectionsMovable(True)
        header.sectionMoved.connect(lambda: save_column_order(self.table, "article_search"))
        self.table.setStyleSheet("QTableWidget { gridline-color: #333; }")
        layout.addWidget(self.table)
        
        # Load column order and widths
        restore_column_order(self.table, "article_search")
        self._restore_column_widths()
        
        # Connect double click
        self.table.cellDoubleClicked.connect(self.handle_double_click)
        
        footer = QHBoxLayout()
        self.status_label = QLabel("Inserisci i termini di ricerca (logica AND) e premi Invio. Usa % per 'contiene'.")
        self.status_label.setStyleSheet("color: #888; font-style: italic;")
        footer.addWidget(self.status_label)
        
        layout.addLayout(footer)

    def perform_search(self):
        text = self.search_input.text().strip()
        if not text: return
        
        words = text.split()
        session = self.parent().db_manager.get_session()
        try:
            from database import RigaFattura, Fattura
            query = session.query(RigaFattura).join(Fattura)
            
            search_code = self.cb_code.isChecked()
            search_desc = self.cb_desc.isChecked()
            
            # Default to both if none selected
            if not search_code and not search_desc:
                search_code = True
                search_desc = True

            current_step = {
                'words': words,
                'search_code': search_code,
                'search_desc': search_desc
            }

            if not self.cb_incremental.isChecked():
                self.active_search_steps = [current_step]
            else:
                self.active_search_steps.append(current_step)
                
            # Build query from all steps
            all_conditions = []
            
            for step in self.active_search_steps:
                step_conditions = []
                for word in step['words']:
                    pattern = word if '%' in word else f"%{word}%"
                    field_filters = []
                    if step['search_desc']:
                        field_filters.append(RigaFattura.descrizione.ilike(pattern))
                    if step['search_code']:
                        field_filters.append(RigaFattura.articolo_codice.ilike(pattern))
                    
                    step_conditions.append(or_(*field_filters))
                
                # Combine words in this step with AND
                if step_conditions:
                    all_conditions.append(and_(*step_conditions))
            
            # Combine all steps with AND
            if all_conditions:
                query = query.filter(and_(*all_conditions))
                
            results = query.order_by(Fattura.data.desc(), Fattura.numero.desc()).all()
            
            self.display_results(results)
            
            mode_text = "Incrementale" if self.cb_incremental.isChecked() else "Nuova ricerca"
            self.status_label.setText(f"[{mode_text}] Trovate {len(results)} righe corrispondenti.")
        except Exception as e:
            self.status_label.setText(f"Errore durante la ricerca: {e}")
            if self.cb_incremental.isChecked() and self.active_search_steps:
                 self.active_search_steps.pop() # Remove failed step
        finally:
            session.close()

    def update_search_mode_label(self, state):
        if self.cb_incremental.isChecked():
            self.lbl_mode.setText("Modalità: Ricerca incrementale")
            self.lbl_mode.setStyleSheet("color: #ffb74d; font-weight: bold; margin-left: 10px;")
        else:
            self.lbl_mode.setText("Modalità: Nuova ricerca")
            self.lbl_mode.setStyleSheet("color: #888; font-weight: bold; margin-left: 10px;")

    def display_results(self, results):
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        for row, riga in enumerate(results):
            self.table.insertRow(row)
            
            # Invoice Info
            # Store fattura object in the first column for double-click retrieval
            self.table.setItem(row, 0, make_item(riga.fattura.numero, user_role_data=riga.fattura))
            self.table.setItem(row, 1, make_item(riga.fattura.data.strftime("%d/%m/%Y") if riga.fattura.data else "-", raw_value=riga.fattura.data))
            self.table.setItem(row, 2, make_item(riga.fattura.cliente_denominazione))
            self.table.setItem(row, 3, make_item(riga.fattura.cliente_codice or "-"))
            
            # Item Info
            self.table.setItem(row, 4, make_item(riga.articolo_codice or "-"))
            self.table.setItem(row, 5, make_item(riga.descrizione))
            self.table.setItem(row, 6, make_item(f"{riga.quantita:.2f}" if riga.quantita is not None else "0.00", raw_value=riga.quantita))
            self.table.setItem(row, 7, make_item(f"{riga.prezzo_unitario:.2f} €" if riga.prezzo_unitario is not None else "0.00 €", raw_value=riga.prezzo_unitario))
            self.table.setItem(row, 8, make_item(f"{riga.totale_riga:.2f} €" if riga.totale_riga is not None else "0.00 €", raw_value=riga.totale_riga))
            
            # Action Button
            btn_detail = QPushButton("Dettaglio Fattura")
            btn_detail.setCursor(Qt.PointingHandCursor)
            btn_detail.setStyleSheet("background: #444; color: white; border: none; padding: 5px; border-radius: 3px;")
            # Capture fattura explicitly
            btn_detail.clicked.connect(lambda _, f=riga.fattura: self.open_invoice_detail(f))
            self.table.setCellWidget(row, 9, btn_detail)
        
        self.table.setSortingEnabled(True)

    def handle_double_click(self, row, col):
        """Open invoice detail on double click."""
        item = self.table.item(row, 0)
        if item:
            fattura = item.data(Qt.UserRole)
            if fattura:
                self.open_invoice_detail(fattura)

    def _save_column_widths(self):
        """Save current column widths for article search."""
        prefs = load_column_prefs()
        widths = [self.table.columnWidth(i) for i in range(self.table.columnCount())]
        prefs["article_search_widths"] = widths
        save_column_prefs(prefs)

    def _restore_column_widths(self):
        """Restore saved column widths for article search."""
        prefs = load_column_prefs()
        widths = prefs.get("article_search_widths")
        if widths and len(widths) == self.table.columnCount():
            for i, w in enumerate(widths):
                self.table.setColumnWidth(i, w)
        else:
            # Default reasonable widths
            defaults = [80, 100, 200, 80, 120, 300, 80, 100, 100, 120]
            for i, w in enumerate(defaults):
                if i < self.table.columnCount():
                    self.table.setColumnWidth(i, w)

    def closeEvent(self, event):
        """Save column widths on close."""
        self._save_column_widths()
        super().closeEvent(event)

    def open_invoice_detail(self, fattura):
        dialog = InvoiceDetailDialog(fattura, self.parent())
        dialog.exec()

class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.setWindowTitle("Gestionale Tebo per Angeleri")
        
        # Screen-aware window sizing to prevent oversized window on startup
        screen = QApplication.primaryScreen().availableGeometry()
        # Use 70% of screen width and 80% of screen height, capped at reasonable maximums
        initial_width = min(1000, int(screen.width() * 0.7))
        initial_height = min(700, int(screen.height() * 0.8))
        self.resize(initial_width, initial_height)
        
        # Set minimum size to ensure usability
        self.setMinimumSize(800, 600)
        
        # Center window on screen
        self.move(
            (screen.width() - initial_width) // 2,
            (screen.height() - initial_height) // 2
        )
        
        self.db_manager = db_manager
        
        # Load Preferences (Theme, etc.)
        self.prefs = load_column_prefs()
        self.current_theme = self.prefs.get("theme", "dark")
        
        self.init_ui()
        self.apply_theme(self.current_theme)
        self.detail_windows = {} # Registry for open detail windows

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        self.prefs["theme"] = theme_name
        save_column_prefs(self.prefs)
        
        if theme_name == "dark":
            self.setStyleSheet("""
                QWidget { background-color: #303030; color: #ffffff; font-family: Segoe UI, sans-serif; }
                QFrame#sidebar { background-color: #212121; border-right: 1px solid #424242; }
                QFrame#topbar { background-color: #212121; border-bottom: 1px solid #424242; }
                QTableWidget { gridline-color: #424242; background-color: #303030; }
                QHeaderView::section { background-color: #212121; border: 1px solid #424242; padding: 5px; }
                QPushButton { background-color: #424242; border-radius: 4px; padding: 8px 15px; }
                QPushButton:hover { background-color: #616161; }
                QPushButton:checked { background-color: #00bcd4; color: #000; }
                QLineEdit { background-color: #212121; border: 1px solid #424242; padding: 5px; }
            """)
        else:
            self.setStyleSheet("""
                QWidget { background-color: #f5f5f5; color: #333; font-family: Segoe UI, sans-serif; }
                QFrame#sidebar { background-color: #eeeeee; border-right: 1px solid #ddd; }
                QFrame#topbar { background-color: #eeeeee; border-bottom: 1px solid #ddd; }
                QTableWidget { gridline-color: #ddd; background-color: #ffffff; }
                QHeaderView::section { background-color: #e0e0e0; border: 1px solid #ccc; padding: 5px; }
                QPushButton { background-color: #e0e0e0; border-radius: 4px; padding: 8px 15px; }
                QPushButton:hover { background-color: #d0d0d0; }
                QPushButton:checked { background-color: #00bcd4; color: #fff; }
                QLineEdit { background-color: #ffffff; border: 1px solid #ccc; padding: 5px; }
            """)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        parent_layout = QVBoxLayout(main_widget)
        parent_layout.setContentsMargins(0,0,0,0)
        parent_layout.setSpacing(0)

        # 1. Top Bar (Logo & Title)
        top_bar = QFrame()
        top_bar.setObjectName("topbar")
        top_bar.setFixedHeight(80)
        top_layout = QHBoxLayout(top_bar)
        
        # Left Logo
        logo_left = QLabel()
        logo_left_path = os.path.join(BASE_DIR, "ANGELERI_LOGO_DEFINITIVO.png")
        if os.path.exists(logo_left_path):
            pix = QPixmap(logo_left_path).scaled(150, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_left.setPixmap(pix)
        top_layout.addWidget(logo_left)
        
        top_layout.addStretch()
        
        # Central Title
        title = QLabel("Gestionale TEBO")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #00bcd4;")
        top_layout.addWidget(title)
        
        top_layout.addStretch()
        
        # Right Logo
        logo_right = QLabel()
        logo_right_path = os.path.join(BASE_DIR, "Logo-tebo.png")
        if os.path.exists(logo_right_path):
            pix = QPixmap(logo_right_path).scaled(150, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_right.setPixmap(pix)
        top_layout.addWidget(logo_right)
        
        parent_layout.addWidget(top_bar)

        # Main horizontal area
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        parent_layout.addLayout(main_layout)

        # 2. Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)

        self.nav_btns = []
        self.btn_dashboard = self.create_nav_btn("Dashboard")
        self.btn_clienti = self.create_nav_btn("Clienti")
        self.btn_fornitori = self.create_nav_btn("Fornitori")
        self.btn_articoli = self.create_nav_btn("Articoli")
        self.btn_fatture = self.create_nav_btn("Fatture Clienti")
        self.btn_fatture_fornitori = self.create_nav_btn("Fatture Fornitori", highlight=True)
        self.btn_settings = self.create_nav_btn("Impostazioni")
        
        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_clienti)
        sidebar_layout.addWidget(self.btn_fornitori)
        sidebar_layout.addWidget(self.btn_articoli)
        sidebar_layout.addWidget(self.btn_fatture)
        sidebar_layout.addWidget(self.btn_fatture_fornitori)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.btn_settings)

        main_layout.addWidget(self.sidebar)

        # 3. Content Area (Stacked)
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.setup_dashboard_view()
        self.setup_table_view("clienti")
        self.setup_table_view("fornitori")
        self.setup_table_view("articoli")
        self.setup_table_view("fatture")
        self.setup_table_view("fatture_fornitori")
        self.setup_settings_view()

        # Events - Connections
        self.btn_dashboard.clicked.connect(lambda: self.switch_view(0))
        self.btn_clienti.clicked.connect(lambda: self.switch_view(1))
        self.btn_fornitori.clicked.connect(lambda: self.switch_view(2))
        self.btn_articoli.clicked.connect(lambda: self.switch_view(3))
        self.btn_fatture.clicked.connect(lambda: self.switch_view(4))
        self.btn_fatture_fornitori.clicked.connect(lambda: self.switch_view(5))
        self.btn_settings.clicked.connect(lambda: self.switch_view(6))

        # Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.switch_view(0)

    def create_nav_btn(self, text, highlight=False):
        btn = QPushButton(text)
        btn.setCheckable(True)
        if highlight:
            btn.setStyleSheet("color: #ffb74d;")
        self.nav_btns.append(btn)
        return btn


    def switch_view(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == index)
        
        # Reload data based on view
        if index == 0: self.load_stats()
        elif index == 1: self.load_table_data("clienti")
        elif index == 2: self.load_table_data("fornitori")
        elif index == 3: self.load_table_data("articoli")
        elif index == 4: self.load_table_data("fatture")
        elif index == 5: self.load_table_data("fatture_fornitori")
        elif index == 6: pass

    # --- VIEWS SETUP ---
    def setup_dashboard_view(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        header = QLabel("Dashboard")
        header.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(header)
        
        info = QLabel("Benvenuto nel Gestionale Tebo.\nSeleziona una voce dal menu laterale.")
        layout.addWidget(info)
        
        self.db_info_label = QLabel("Database: -")
        self.db_info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00bcd4; margin-top: 10px;")
        layout.addWidget(self.db_info_label)

        self.stats_label = QLabel("Caricamento statistiche...")
        self.stats_label.setStyleSheet("font-size: 16px; color: #bdbdbd;")
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        self.stack.insertWidget(0, page)

    def setup_table_view(self, type_key):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Header
        top_bar = QHBoxLayout()
        display_name_map = {
            "fatture": "Fatture Clienti",
            "fatture_fornitori": "Fatture Fornitori",
        }
        display_name = display_name_map.get(type_key, type_key.capitalize())
        title = QLabel(display_name)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00bcd4; margin-right: 15px;")
        title.setMinimumWidth(160)
        top_bar.addWidget(title)

        search = QLineEdit()
        search.setPlaceholderText("Cerca...")
        search.textChanged.connect(lambda t, k=type_key: self.filter_table(k, t))
        search.setObjectName(f"search_{type_key}")
        if type_key == "fatture_fornitori":
            search.setMinimumWidth(160)
        top_bar.addWidget(search)
        top_bar.setStretchFactor(search, 2)  # La search prende il doppio dello spazio libero

        # Advanced Filters
        if type_key == "articoli":
            top_bar.addWidget(QLabel("Prezzo Min:"))
            p_min = QLineEdit()
            p_min.setFixedWidth(60)
            p_min.setObjectName(f"filter_pmin_{type_key}")
            p_min.textChanged.connect(lambda t: self.filter_table(type_key, search.text()))
            top_bar.addWidget(p_min)
            
            top_bar.addWidget(QLabel("Max:"))
            p_max = QLineEdit()
            p_max.setFixedWidth(60)
            p_max.setObjectName(f"filter_pmax_{type_key}")
            p_max.textChanged.connect(lambda t: self.filter_table(type_key, search.text()))
            top_bar.addWidget(p_max)
            
        elif type_key == "fatture":
            top_bar.addWidget(QLabel("Dal:"))
            d_start = QDateEdit()
            d_start.setCalendarPopup(True)
            d_start.setDate(QDate(2020, 1, 1))
            d_start.setObjectName(f"filter_dstart_{type_key}")
            d_start.dateChanged.connect(lambda d: self.filter_table(type_key, search.text()))
            top_bar.addWidget(d_start)
            
            top_bar.addWidget(QLabel("Al:"))
            d_end = QDateEdit()
            d_end.setCalendarPopup(True)
            d_end.setDate(QDate.currentDate())
            d_end.setObjectName(f"filter_dend_{type_key}")
            d_end.dateChanged.connect(lambda d: self.filter_table(type_key, search.text()))
            top_bar.addWidget(d_end)
            
            # Article Search Button
            btn_search_art = QPushButton("🔍 Ricerca Articolo")
            btn_search_art.setCursor(Qt.PointingHandCursor)
            btn_search_art.setStyleSheet("""
                QPushButton {
                    background-color: #00bcd4;
                    color: white;
                    font-weight: bold;
                    padding: 0 15px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #00acc1;
                }
            """)
            btn_search_art.setFixedHeight(30)
            btn_search_art.clicked.connect(self.open_article_search)
            top_bar.addWidget(btn_search_art)

        elif type_key == "fatture_fornitori":
            pass  # filtri e pulsanti vanno nell'action_bar (riga 2)

        # Column config button (riga 1, sempre)
        btn_config = QPushButton("⚙")
        btn_config.setFixedSize(36, 36)
        btn_config.setStyleSheet("font-size: 18px; padding: 0;")
        btn_config.setToolTip("Configura colonne visibili")
        btn_config.clicked.connect(lambda checked, k=type_key: self.open_column_config(k))
        top_bar.addWidget(btn_config)

        layout.addLayout(top_bar)

        # ── RIGA 2: filtri + toggle + pulsanti azione (solo fatture_fornitori) ──
        if type_key == "fatture_fornitori":
            action_bar = QHBoxLayout()
            action_bar.setSpacing(8)

            # Filtri data
            lbl_dal = QLabel("Dal:")
            lbl_dal.setStyleSheet("color: #ccc;")
            action_bar.addWidget(lbl_dal)
            d_start_ff = QDateEdit()
            d_start_ff.setCalendarPopup(True)
            d_start_ff.setDate(QDate(2020, 1, 1))
            d_start_ff.setObjectName("filter_dstart_fatture_fornitori")
            d_start_ff.setFixedHeight(28)
            d_start_ff.dateChanged.connect(lambda d: self.filter_table(
                "fatture_fornitori",
                self.findChild(QLineEdit, "search_fatture_fornitori").text()
                if self.findChild(QLineEdit, "search_fatture_fornitori") else ""))
            action_bar.addWidget(d_start_ff)

            lbl_al = QLabel("Al:")
            lbl_al.setStyleSheet("color: #ccc;")
            action_bar.addWidget(lbl_al)
            d_end_ff = QDateEdit()
            d_end_ff.setCalendarPopup(True)
            d_end_ff.setDate(QDate.currentDate())
            d_end_ff.setObjectName("filter_dend_fatture_fornitori")
            d_end_ff.setFixedHeight(28)
            d_end_ff.dateChanged.connect(lambda d: self.filter_table(
                "fatture_fornitori",
                self.findChild(QLineEdit, "search_fatture_fornitori").text()
                if self.findChild(QLineEdit, "search_fatture_fornitori") else ""))
            action_bar.addWidget(d_end_ff)

            # Toggle Escludi Servizi
            btn_escludi = QPushButton("⚡ Escludi Servizi")
            btn_escludi.setCheckable(True)
            btn_escludi.setObjectName("btn_escludi_servizi_ff")
            btn_escludi.setCursor(Qt.PointingHandCursor)
            btn_escludi.setFixedHeight(28)
            btn_escludi.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3a;
                    color: #aaa;
                    font-weight: bold;
                    padding: 0 16px;
                    border-radius: 4px;
                    border: 1px solid #555;
                }
                QPushButton:checked {
                    background-color: #f57c00;
                    color: white;
                    border: 1px solid #e65100;
                }
                QPushButton:hover:!checked { background-color: #505050; }
            """)
            _prefs_ff = load_column_prefs()
            btn_escludi.setChecked(_prefs_ff.get("escludi_servizi_ff", False))
            btn_escludi.toggled.connect(lambda checked: (
                save_column_prefs({**load_column_prefs(), "escludi_servizi_ff": checked}),
                self.filter_table(
                    "fatture_fornitori",
                    self.findChild(QLineEdit, "search_fatture_fornitori").text()
                    if self.findChild(QLineEdit, "search_fatture_fornitori") else "")
            ))
            action_bar.addWidget(btn_escludi)

            action_bar.addStretch()

            # Helper per pulsanti azione
            def _make_btn(label, tooltip, bg, hover, fg="black"):
                b = QPushButton(label)
                b.setCursor(Qt.PointingHandCursor)
                b.setToolTip(tooltip)
                b.setFixedHeight(28)
                b.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {bg};
                        color: {fg};
                        font-weight: bold;
                        padding: 0 16px;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{ background-color: {hover}; }}
                """)
                return b

            btn_import_sdi = _make_btn(
                "⬇ Carica SDI", "Carica singoli file SDI (.p7m / .xml)",
                "#ffb74d", "#ffa726")
            btn_import_sdi.clicked.connect(self.import_sdi_files)
            action_bar.addWidget(btn_import_sdi)

            btn_import_folder = _make_btn(
                "📂 Importa Cartella", "Importa ricorsivamente una cartella SDI",
                "#ffcc80", "#ffb74d")
            btn_import_folder.clicked.connect(self.import_sdi_folder)
            action_bar.addWidget(btn_import_folder)

            btn_clear = _make_btn(
                "🗑 Svuota Fatture", "Elimina tutte le fatture fornitori dal database",
                "#ef5350", "#e53935", "white")
            btn_clear.clicked.connect(self.clear_all_fatture_acquisto)
            action_bar.addWidget(btn_clear)

            layout.addLayout(action_bar)


        # Barra totali (solo per fatture_fornitori)
        if type_key == "fatture_fornitori":
            totals_bar = QHBoxLayout()
            lbl_totals_visible = QLabel("Visibili: — fatture — € —")
            lbl_totals_visible.setObjectName("lbl_totals_visible_ff")
            lbl_totals_visible.setStyleSheet("color: #ffb74d; font-weight: bold; font-size: 13px; margin: 4px 10px;")
            lbl_totals_complete = QLabel("Vista completa: — fatture — € —")
            lbl_totals_complete.setObjectName("lbl_totals_complete_ff")
            lbl_totals_complete.setStyleSheet("color: #888; font-size: 12px; margin: 4px 10px;")
            totals_bar.addWidget(lbl_totals_visible)
            totals_bar.addWidget(QLabel("|"))
            totals_bar.addWidget(lbl_totals_complete)
            totals_bar.addStretch()
            layout.addLayout(totals_bar)

        # Table
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsMovable(True)
        table.horizontalHeader().sectionMoved.connect(lambda: save_column_order(table, type_key))
        table.setSortingEnabled(True)
        table.setObjectName(f"table_{type_key}")
        
        # Connect Actions
        if type_key == "fatture":
            table.cellDoubleClicked.connect(self.open_invoice_detail)
            table.cellClicked.connect(self.handle_invoice_table_click)
        elif type_key == "clienti":
            table.cellDoubleClicked.connect(self.open_client_detail)
            table.cellClicked.connect(self.handle_client_table_click)
        elif type_key == "fornitori":
            table.cellDoubleClicked.connect(self.open_supplier_detail)
        elif type_key == "articoli":
            table.cellDoubleClicked.connect(self.open_article_detail)
            table.cellClicked.connect(self.handle_article_table_click)
        elif type_key == "fatture_fornitori":
            table.cellDoubleClicked.connect(self.open_invoice_detail)
            table.cellClicked.connect(self.handle_invoice_table_click)

        layout.addWidget(table)
        self.stack.addWidget(page)

    def open_article_search(self):
        dialog = ArticleSearchDialog(self)
        dialog.exec()

    def import_sdi_files(self):
        """Apre un dialogo per selezionare file .p7m o .xml e li importa."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleziona Fatture Elettroniche", "", "Fatture Elettroniche (*.p7m *.xml);;Tutti i file (*.*)"
        )
        if not files: return
        
        from data_manager import DataManager
        dm = DataManager(self.db_manager)
        
        success_count = 0
        errors = []
        
        for f in files:
            success, msg = dm.import_fattura_acquisto_p7m(f)
            if success:
                success_count += 1
            else:
                errors.append(f"{os.path.basename(f)}: {msg}")
        
        if success_count > 0:
            self.load_table_data("fatture_fornitori")
            self.load_stats()
            
        if not errors:
            QMessageBox.information(self, "Importazione Completata", f"Importate {success_count} fatture correttamente.")
        else:
            err_msg = "\n".join(errors)
            QMessageBox.warning(self, "Esito Importazione", f"Importate {success_count} fatture.\n\nErrori:\n{err_msg}")

    def import_sdi_folder(self):
        """Apre un dialogo per selezionare una cartella e importa ricorsivamente tutte le SDI."""
        folder = QFileDialog.getExistingDirectory(self, "Seleziona Cartella Fatture SDI")
        if not folder: return
        
        from PySide6.QtWidgets import QProgressDialog
        
        progress = QProgressDialog("Scansione cartelle...", "Annulla", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setWindowTitle("Importazione Massiva SDI")
        progress.show()
        
        from data_manager import DataManager
        dm = DataManager(self.db_manager)
        
        def update_progress(current, total, filename):
            progress.setMaximum(total)
            progress.setValue(current)
            progress.setLabelText(f"Importazione: {filename} ({current}/{total})")
            QApplication.processEvents()
            
        success, errors_count, error_list = dm.batch_import_from_folders([folder], progress_callback=update_progress)
        
        progress.setValue(progress.maximum())
        
        if success > 0:
            self.load_table_data("fatture_fornitori")
            self.load_stats()
            
        if not error_list:
            QMessageBox.information(self, "Importazione Completata", f"Importazione terminata.\nFatture caricate con successo: {success}")
        else:
            err_msg = "\n".join(error_list[:10])
            if len(error_list) > 10:
                err_msg += f"\n... e altri {len(error_list)-10} errori."
            QMessageBox.warning(self, "Esito Importazione Massiva", 
                                f"Fatture caricate: {success}\nErrori riscontrati: {errors_count}\n\nAnteprima Errori:\n{err_msg}")

    def clear_all_fatture_acquisto(self):
        """Chiede conferma e svuota tutte le fatture fornitori dal database."""
        reply = QMessageBox.warning(self, "Conferma Cancellazione", 
                                  "Questa azione eliminerà DEFINITIVAMENTE tutte le fatture fornitori e le relative righe dettaglio.\n\nVuoi procedere?",
                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            dm = DataManager(self.db_manager)
            success, msg = dm.delete_all_fatture_acquisto()
            if success:
                QMessageBox.information(self, "Svuotamento Completato", msg)
                self.load_table_data("fatture_fornitori")
                self.load_stats()
            else:
                QMessageBox.critical(self, "Errore", msg)

    def import_pdf_robecchi_ui(self):
        """Avvia l'import PDF Robecchi con progress dialog e popup riepilogo."""
        from PySide6.QtWidgets import QProgressDialog

        # Cartella di default (ultima usata, o percorso Robecchi standard)
        prefs = load_column_prefs()
        default_folder = prefs.get(
            'robecchi_pdf_folder',
            r'I:\Il mio Drive\TEBO\02 Fornitori\Fatture Fornitori\Robecchi'
        )

        folder = QFileDialog.getExistingDirectory(
            self, "Seleziona Cartella PDF Robecchi", default_folder
        )
        if not folder:
            return

        # Salva la cartella scelta per la prossima volta
        prefs['robecchi_pdf_folder'] = folder
        save_column_prefs(prefs)

        progress = QProgressDialog("Scansione PDF...", "Annulla", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setWindowTitle("Sincronizzazione PDF Robecchi")
        progress.show()
        QApplication.processEvents()

        dm = DataManager(self.db_manager)
        cancelled = [False]

        def update_progress(current, total, filename):
            if progress.wasCanceled():
                cancelled[0] = True
                return
            progress.setMaximum(max(total, 1))
            progress.setValue(current)
            progress.setLabelText(f"Elaborazione: {filename} ({current + 1}/{total})")
            QApplication.processEvents()

        result = dm.import_pdf_robecchi(folder, progress_callback=update_progress)

        progress.setValue(progress.maximum())
        progress.close()

        if result['imported'] > 0:
            self.load_table_data('fatture_fornitori')
            self.load_stats()

        # Popup riepilogo
        imported = result['imported']
        rows    = result['rows']
        skipped = result['skipped']
        errors  = result['errors']

        summary = (
            f"✅  {imported} fatture/ordini importati\n"
            f"📦  {rows} righe articolo caricate\n"
            f"⏭  {skipped} file saltati (scansioni / offerte / duplicati)\n"
            f"❌  {len(errors)} errori di lettura"
        )

        if errors:
            err_detail = '\n'.join(f'• {n}: {m}' for n, m in errors[:10])
            if len(errors) > 10:
                err_detail += f'\n... e altri {len(errors) - 10} errori.'
            summary += f'\n\nDettaglio errori:\n{err_detail}'
            QMessageBox.warning(self, "Processo completato", summary)
        else:
            QMessageBox.information(self, "Processo completato", summary)


    def setup_settings_view(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        header = QLabel("Impostazioni")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #00bcd4; margin-bottom: 20px;")
        layout.addWidget(header)
        
        # Theme section
        theme_group = QGroupBox("Interfaccia")
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.addWidget(QLabel("Seleziona il tema dell'applicazione:"))
        
        theme_selector = QComboBox()
        theme_selector.addItems(["Scuro", "Chiaro"])
        theme_selector.setCurrentText("Scuro" if self.current_theme == "dark" else "Chiaro")
        theme_selector.currentTextChanged.connect(lambda t: self.apply_theme("dark" if t == "Scuro" else "light"))
        theme_layout.addWidget(theme_selector)
        layout.addWidget(theme_group)
        
        # Database selection section
        db_group = QGroupBox("Configurazione Database")
        db_layout = QVBoxLayout(db_group)
        db_layout.addWidget(QLabel("Seleziona il file database (.db) da utilizzare:"))
        
        btn_db = QPushButton("📂 Cambia Database...")
        btn_db.setStyleSheet("height: 35px;")
        btn_db.clicked.connect(self.change_db_path)
        db_layout.addWidget(btn_db)
        layout.addWidget(db_group)

        # Data Management section
        import_group = QGroupBox("Manutenzione Dati")
        import_layout = QVBoxLayout(import_group)
        warn_lbl = QLabel("ATTENZIONE: le importazioni sovrascrivono i dati esistenti.")
        warn_lbl.setStyleSheet("color: #e65100; font-weight: bold; margin-bottom: 4px;")
        import_layout.addWidget(warn_lbl)

        _BTN_H = "min-height: 36px; padding: 4px 12px; font-weight: bold;"

        btn_import = QPushButton("Importa Dati da Excel (Clienti / Fornitori / Articoli)")
        btn_import.setStyleSheet(f"background-color: #ffb74d; color: #1a1a1a; {_BTN_H}")
        btn_import.clicked.connect(self.run_import)
        import_layout.addWidget(btn_import)

        # --- Import SDI ---
        sdi_hl = QHBoxLayout()
        sdi_hl.setSpacing(8)

        btn_sdi_file = QPushButton("Importa File SDI  (.xml / .p7m)")
        btn_sdi_file.setStyleSheet(f"background-color: #455a64; color: #eceff1; {_BTN_H}")
        btn_sdi_file.clicked.connect(self.import_sdi_files)
        sdi_hl.addWidget(btn_sdi_file)

        btn_sdi_folder = QPushButton("Importa Cartella SDI  (ricorsivo)")
        btn_sdi_folder.setStyleSheet(f"background-color: #455a64; color: #eceff1; {_BTN_H}")
        btn_sdi_folder.clicked.connect(self.import_sdi_folder)
        sdi_hl.addWidget(btn_sdi_folder)
        import_layout.addLayout(sdi_hl)

        # --- Import PDF Robecchi ---
        btn_pdf_robecchi = QPushButton("Sincronizza PDF Robecchi  (fatture e conferme d'ordine)")
        btn_pdf_robecchi.setStyleSheet(
            f"background-color: #1565c0; color: white; {_BTN_H}"
        )
        btn_pdf_robecchi.setToolTip("Importa fatture e conferme d'ordine PDF da Robecchi Articoli Tecnici")
        btn_pdf_robecchi.clicked.connect(self.import_pdf_robecchi_ui)
        import_layout.addWidget(btn_pdf_robecchi)

        import_layout.addSpacing(6)

        btn_clear = QPushButton("Svuota tutte le Fatture Fornitori")
        btn_clear.setStyleSheet(f"background-color: #b71c1c; color: white; {_BTN_H}")
        btn_clear.clicked.connect(self.clear_all_fatture_acquisto)
        import_layout.addWidget(btn_clear)

        layout.addWidget(import_group)

        # Lista Esclusione Servizi
        excl_group = QGroupBox("Filtro Esclusione Servizi — Lista Fornitori")
        excl_layout = QVBoxLayout(excl_group)
        excl_layout.addWidget(QLabel("Un nome per riga (o parte del nome). Usato dal toggle 'Escludi Servizi' in Fatture Fornitori:"))

        from PySide6.QtWidgets import QTextEdit
        txt_excl = QTextEdit()
        txt_excl.setObjectName("txt_lista_esclusione")
        txt_excl.setMaximumHeight(150)
        txt_excl.setPlaceholderText("Es.:\nTIM\nENEL\nESSELUNGA")
        # Carica lista corrente
        _prefs_s = load_column_prefs()
        _lista_corrente = _prefs_s.get("lista_esclusione_servizi", FORNITORI_SERVIZIO_DEFAULT)
        txt_excl.setPlainText("\n".join(_lista_corrente))
        excl_layout.addWidget(txt_excl)

        btn_save_excl = QPushButton("💾 Salva Lista Esclusione")
        btn_save_excl.setStyleSheet("height: 35px; background-color: #388e3c; color: white; font-weight: bold;")
        def _save_excl_list():
            lines = [l.strip() for l in txt_excl.toPlainText().splitlines() if l.strip()]
            p = load_column_prefs()
            p["lista_esclusione_servizi"] = lines
            save_column_prefs(p)
            QMessageBox.information(self, "Lista salvata", f"Lista aggiornata con {len(lines)} voci.")
        btn_save_excl.clicked.connect(_save_excl_list)
        excl_layout.addWidget(btn_save_excl)

        btn_reset_excl = QPushButton("↺ Ripristina Lista Predefinita")
        btn_reset_excl.setStyleSheet("height: 30px;")
        def _reset_excl_list():
            txt_excl.setPlainText("\n".join(FORNITORI_SERVIZIO_DEFAULT))
        btn_reset_excl.clicked.connect(_reset_excl_list)
        excl_layout.addWidget(btn_reset_excl)

        layout.addWidget(excl_group)

        layout.addStretch()
        self.stack.addWidget(page)

    # --- LOGIC ---
    def load_stats(self):
        # Update DB path info
        self.db_info_label.setText(f"File Database Attivo:\n{self.db_manager.db_path}")

        session = self.db_manager.get_session()
        try:
            c_count = session.query(Cliente).count()
            f_count = session.query(Fornitore).count()
            a_count = session.query(Articolo).count()
            v_count = session.query(Fattura).filter_by(tipo='VENDITA').count()
            p_count = session.query(Fattura).filter_by(tipo='ACQUISTO').count()
            
            stats_text = (
                f"Statistiche Rapide:\n"
                f"- Clienti: {c_count}\n"
                f"- Fornitori: {f_count}\n"
                f"- Articoli: {a_count}\n"
                f"- Fatture Clienti: {v_count}\n"
                f"- Fatture Fornitori (SDI): {p_count}"
            )
            self.stats_label.setText(stats_text)
        except Exception as e:
            self.stats_label.setText(f"Errore connessione db: {e}")
        finally:
            session.close()

    def get_table_widget(self, index):
        key_map = {1: "clienti", 2: "fornitori", 3: "articoli", 4: "fatture", 5: "fatture_fornitori"}
        key = key_map.get(index)
        if not key: return None
        page = self.stack.widget(index)
        return page.findChild(QTableWidget, f"table_{key}")

    TABLE_COLUMNS = {
        "clienti": [
            "ID", "Codice", "Codice Alternativo", "Ragione Sociale", "Indirizzo", "CAP", "Località", "Provincia", 
            "Partita IVA", "Codice Fiscale", "Telefono", "Email", "Cellulare", "Pagamento", "Banca", "IBAN", "Agente", "Listino", "Azioni"
        ],
        "fornitori": [
            "ID", "Codice", "Ragione Sociale", "Indirizzo Esteso", "Indirizzo", "CAP", "Località", "PR", "Nazione",
            "Codice Fiscale", "Partita IVA", "IVA Intra", "Telefono", "Fax", "Pagamento", "Descrizione Pagamento",
            "Banca", "Filiale", "ABI", "CAB", "Conto Corrente", "IBAN", "Porto", "Spedizione", "Email"
        ],
        "articoli": ["Codice", "Descrizione", "Prezzo", "UM", "Azioni"],
        "fatture": ["ID", "Numero", "Data", "Codice Cliente", "Cliente", "Causale", "Totale", "Azioni"],
        "fatture_fornitori": ["ID", "Numero", "Data", "Codice Forn.", "Fornitore", "Causale", "Totale", "Azioni"],
    }

    def load_table_data(self, type_key):
        table = self.findChild(QTableWidget, f"table_{type_key}")
        if not table: return
        
        prefs = load_column_prefs()
        visible_cols = prefs.get(f"visible_{type_key}", self.TABLE_COLUMNS[type_key])
        
        all_cols = self.TABLE_COLUMNS[type_key]
        table.setColumnCount(len(all_cols))
        table.setHorizontalHeaderLabels(all_cols)
        restore_column_order(table, type_key)
        
        for i, col in enumerate(all_cols):
            table.setColumnHidden(i, col not in visible_cols)
            
        session = self.db_manager.get_session()
        try:
            items = []
            if type_key == "clienti": items = session.query(Cliente).all()
            elif type_key == "fornitori": items = session.query(Fornitore).all()
            elif type_key == "articoli": items = session.query(Articolo).all()
            elif type_key == "fatture": items = session.query(Fattura).filter_by(tipo='VENDITA').order_by(Fattura.data.desc()).all()
            elif type_key == "fatture_fornitori": items = session.query(Fattura).filter_by(tipo='ACQUISTO').order_by(Fattura.data.desc()).all()
            
            table.setRowCount(len(items))
            for i, obj in enumerate(items):
                if type_key == "clienti":
                    table.setItem(i, 0, make_item(obj.id, user_role_data=obj.id))
                    table.setItem(i, 1, make_item(obj.codice))
                    table.setItem(i, 2, make_item(obj.codice_alternativo))
                    table.setItem(i, 3, make_item(obj.ragione_sociale))
                    table.setItem(i, 4, make_item(obj.indirizzo))
                    table.setItem(i, 5, make_item(obj.cap))
                    table.setItem(i, 6, make_item(obj.localita))
                    table.setItem(i, 7, make_item(obj.provincia))
                    table.setItem(i, 8, make_item(obj.partita_iva))
                    table.setItem(i, 9, make_item(obj.codice_fiscale))
                    table.setItem(i, 10, make_item(obj.telefono))
                    table.setItem(i, 11, make_item(obj.email))
                    table.setItem(i, 12, make_item(obj.cellulare))
                    table.setItem(i, 13, make_item(obj.pagamento))
                    table.setItem(i, 14, make_item(obj.banca))
                    table.setItem(i, 15, make_item(obj.iban))
                    table.setItem(i, 16, make_item(obj.agente))
                    table.setItem(i, 17, make_item(obj.listino))
                    # Actions
                    act_item = QTableWidgetItem("📄 Fatture")
                    act_item.setForeground(QColor("#ffb74d"))
                    table.setItem(i, 18, act_item)
                
                elif type_key == "fornitori":
                    table.setItem(i, 0, make_item(obj.id, user_role_data=obj.id))
                    table.setItem(i, 1, make_item(obj.codice))
                    table.setItem(i, 2, make_item(obj.ragione_sociale))
                    table.setItem(i, 3, make_item(obj.indirizzo_esteso))
                    table.setItem(i, 4, make_item(obj.indirizzo))
                    table.setItem(i, 5, make_item(obj.cap))
                    table.setItem(i, 6, make_item(obj.localita))
                    table.setItem(i, 7, make_item(obj.provincia))
                    table.setItem(i, 8, make_item(obj.nazione))
                    table.setItem(i, 9, make_item(obj.codice_fiscale))
                    table.setItem(i, 10, make_item(obj.partita_iva))
                    table.setItem(i, 11, make_item(obj.partita_iva_intra))
                    table.setItem(i, 12, make_item(obj.telefono))
                    table.setItem(i, 13, make_item(obj.fax))
                    table.setItem(i, 14, make_item(obj.pagamento))
                    table.setItem(i, 15, make_item(obj.descrizione_pagamento))
                    table.setItem(i, 16, make_item(obj.banca))
                    table.setItem(i, 17, make_item(obj.filiale))
                    table.setItem(i, 18, make_item(obj.abi))
                    table.setItem(i, 19, make_item(obj.cab))
                    table.setItem(i, 20, make_item(obj.conto_corrente))
                    table.setItem(i, 21, make_item(obj.iban))
                    table.setItem(i, 22, make_item(obj.porto))
                    table.setItem(i, 23, make_item(obj.spedizione))
                    table.setItem(i, 24, make_item(obj.email))

                elif type_key == "articoli":
                    table.setItem(i, 0, make_item(obj.codice, user_role_data=obj.id))
                    table.setItem(i, 1, make_item(obj.descrizione))
                    table.setItem(i, 2, make_item(f"€ {obj.prezzo:.2f}", raw_value=obj.prezzo))
                    table.setItem(i, 3, make_item(obj.um))
                    # Actions
                    act_item = QTableWidgetItem("👁 Vedi")
                    act_item.setForeground(QColor("#00bcd4"))
                    table.setItem(i, 4, act_item)
                    
                elif type_key == "fatture":
                    table.setItem(i, 0, make_item(obj.id, user_role_data=obj.id))
                    table.setItem(i, 1, make_item(obj.numero))
                    table.setItem(i, 2, make_item(obj.data.strftime("%d/%m/%Y") if obj.data else "-", raw_value=obj.data))
                    table.setItem(i, 3, make_item(obj.cliente_codice or ""))
                    table.setItem(i, 4, make_item(obj.cliente_denominazione or ""))
                    table.setItem(i, 5, make_item(obj.causale or ""))
                    table.setItem(i, 6, make_item(f"€ {obj.totale:.2f}", raw_value=obj.totale))
                    # Actions
                    act_item = QTableWidgetItem("👤 Cliente")
                    act_item.setForeground(QColor("#00bcd4"))
                    table.setItem(i, 7, act_item)

                elif type_key == "fatture_fornitori":
                    table.setItem(i, 0, make_item(obj.id, user_role_data=obj.id))
                    table.setItem(i, 1, make_item(obj.numero))
                    table.setItem(i, 2, make_item(obj.data.strftime("%d/%m/%Y") if obj.data else "-", raw_value=obj.data))
                    table.setItem(i, 3, make_item(obj.fornitore_codice or ""))
                    table.setItem(i, 4, make_item(obj.fornitore_denominazione or ""))
                    table.setItem(i, 5, make_item(obj.causale or ""))
                    table.setItem(i, 6, make_item(f"€ {obj.totale:.2f}", raw_value=obj.totale))
                    # Actions
                    act_item = QTableWidgetItem("📦 Fornitore")
                    act_item.setForeground(QColor("#ffb74d"))
                    table.setItem(i, 7, act_item)

        finally:
            session.close()

    def open_column_config(self, type_key):
        prefs = load_column_prefs()
        current_visible = prefs.get(f"visible_{type_key}", self.TABLE_COLUMNS[type_key])
        
        dlg = ColumnConfigDialog(self.TABLE_COLUMNS[type_key], current_visible, self)
        if dlg.exec():
            new_visible = dlg.get_visible_columns()
            prefs[f"visible_{type_key}"] = new_visible
            save_column_prefs(prefs)
            self.load_table_data(type_key)

    def open_invoice_detail(self, row, col):
        table = self.sender() # Getting the table that sent the signal
        if not isinstance(table, QTableWidget): 
            # Fallback if called manually or with different sender
            table = self.get_table_widget(4)
            
        inv_id = None
        for c in range(table.columnCount()):
            item = table.item(row, c)
            if item and item.data(Qt.UserRole) is not None:
                inv_id = item.data(Qt.UserRole)
                break
        
        if not inv_id:
            QMessageBox.warning(self, "Errore", "ID fattura non trovato. Assicurati che la colonna 'ID' sia visibile.")
            return
            
        session = self.db_manager.get_session()
        try:
            # We use lazy joining to avoid DetachedInstanceError in dialog if needed, 
            # though the dialog has its own session now.
            fattura = session.get(Fattura, inv_id)
            if fattura:
                # Use a specific window ID to allow multiple instances
                prefix = "invoice_buy" if fattura.tipo == 'ACQUISTO' else "invoice_sell"
                self.show_detail_window(f"{prefix}_{inv_id}", InvoiceDetailDialog, fattura)
            else:
                QMessageBox.warning(self, "Errore", "Fattura non trovata.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", str(e))
        finally:
            session.close()

    def open_client_detail(self, row, col):
        table = self.sender()
        cli_id = None
        for c in range(table.columnCount()):
            item = table.item(row, c)
            if item and item.data(Qt.UserRole) is not None:
                cli_id = item.data(Qt.UserRole)
                break
        
        if not cli_id:
            QMessageBox.warning(self, "Errore", "ID cliente non trovato. Assicurati che la colonna 'ID' sia visibile.")
            return
            
        session = self.db_manager.get_session()
        try:
            cliente = session.get(Cliente, cli_id)
            if cliente:
                self.show_detail_window(f"client_{cli_id}", ClientDetailDialog, cliente)
            else:
                QMessageBox.warning(self, "Errore", "Cliente non trovato.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", str(e))
        finally:
            session.close()

    def open_supplier_detail(self, row, col):
        table = self.get_table_widget(2) # Fornitori
        item = table.item(row, 0)
        if not item:
            QMessageBox.warning(self, "Errore", "ID fornitore non trovato. Assicurati che la colonna 'ID' sia visibile.")
            return
        
        supplier_id = item.data(Qt.UserRole)
        session = self.db_manager.get_session()
        try:
            supplier = session.get(Fornitore, supplier_id)
            if supplier:
                self.show_detail_window(f"supplier_{supplier_id}", SupplierDetailDialog, supplier)
            else:
                QMessageBox.warning(self, "Errore", "Fornitore non trovato.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", str(e))
        finally:
            session.close()

    def open_article_detail(self, row, col):
        table = self.get_table_widget(3) # Articoli
        item = table.item(row, 0)
        if not item: return
        
        # In Articoli, the code is used as unique identifier usually, 
        # but let's use the DB ID if we set it in UserRole.
        # Looking at load_table_data, I need to set UserRole for Articoli ID.
        article_id = item.data(Qt.UserRole)
        if not article_id:
            # Fallback to code if ID is not in UserRole
            code = item.text()
            session = self.db_manager.get_session()
            article = session.query(Articolo).filter_by(codice=code).first()
            session.close()
        else:
            session = self.db_manager.get_session()
            article = session.get(Articolo, article_id)
            session.close()
        
        if article:
            self.show_detail_window(f"article_{article.id}", ArticleDetailDialog, article)

    def change_db_path(self):
        """Open a file dialog to select a new database file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Database", "", "Database SQLite (*.db);;Tutti i file (*.*)"
        )
        if file_path:
            self.reconnect_db(file_path)

    def reconnect_db(self, path):
        """Reconnect the application to a different database path."""
        if not os.path.exists(path):
            QMessageBox.warning(self, "Errore", f"Il file database specificato non esiste:\n{path}")
            return

        try:
            new_db_man = DatabaseManager(path)
            # Test connection
            session = new_db_man.get_session()
            session.query(Cliente).first() # Simple query to check if it's a valid DB
            session.close()
            
            # If successful, switch
            self.db_manager = new_db_man
            self.prefs["db_path"] = path
            save_column_prefs(self.prefs)
            
            self.load_stats()
            # Also clear open detail windows as they reference the old DB
            for win in list(self.detail_windows.values()):
                win.close()
            self.detail_windows.clear()
            
            QMessageBox.information(self, "Database Aggiornato", f"Connessione stabilita con successo a:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore Database", f"Impossibile collegarsi al database:\n{e}")

    def filter_table(self, key, text):
        idx_map = {"clienti": 1, "fornitori": 2, "articoli": 3, "fatture": 4, "fatture_fornitori": 5}
        table = self.get_table_widget(idx_map.get(key))
        if not table: return

        # Advanced Filter Values
        p_min = -1.0
        p_max = 9999999.0
        d_start = QDate(1900, 1, 1)
        d_end = QDate(2100, 1, 1)
        escludi_servizi = False

        if key == "articoli":
            pmin_edit = self.findChild(QLineEdit, f"filter_pmin_{key}")
            pmax_edit = self.findChild(QLineEdit, f"filter_pmax_{key}")
            if pmin_edit and pmin_edit.text():
                try: p_min = float(pmin_edit.text().replace(',', '.'))
                except: pass
            if pmax_edit and pmax_edit.text():
                try: p_max = float(pmax_edit.text().replace(',', '.'))
                except: pass
        elif key == "fatture":
            dstart_edit = self.findChild(QDateEdit, f"filter_dstart_{key}")
            dend_edit = self.findChild(QDateEdit, f"filter_dend_{key}")
            if dstart_edit: d_start = dstart_edit.date()
            if dend_edit: d_end = dend_edit.date()
        elif key == "fatture_fornitori":
            dstart_edit = self.findChild(QDateEdit, "filter_dstart_fatture_fornitori")
            dend_edit   = self.findChild(QDateEdit, "filter_dend_fatture_fornitori")
            if dstart_edit: d_start = dstart_edit.date()
            if dend_edit:   d_end   = dend_edit.date()
            btn_escludi = self.findChild(QPushButton, "btn_escludi_servizi_ff")
            escludi_servizi = btn_escludi.isChecked() if btn_escludi else False

        # Lista esclusione: usa prefs o default
        prefs = load_column_prefs()
        lista_esclusione = [x.upper() for x in prefs.get("lista_esclusione_servizi", FORNITORI_SERVIZIO_DEFAULT)]

        totale_completo = 0.0
        count_completo = 0
        totale_visibile = 0.0
        count_visibile = 0

        for i in range(table.rowCount()):
            # Text Search Match
            text_match = not text
            for j in range(table.columnCount()):
                if not table.isColumnHidden(j):
                    item = table.item(i, j)
                    if item and text.lower() in item.text().lower():
                        text_match = True
                        break

            # Advanced Matches
            adv_match = True
            if key == "articoli":
                item_price = table.item(i, 2)
                if item_price:
                    price = item_price.data(Qt.UserRole + 1)
                    if price is not None:
                        if price < p_min or price > p_max:
                            adv_match = False
            elif key == "fatture":
                item_date = table.item(i, 2)
                if item_date:
                    date_val = item_date.data(Qt.UserRole + 1)
                    if date_val:
                        qdate = QDate(date_val.year, date_val.month, date_val.day)
                        if qdate < d_start or qdate > d_end:
                            adv_match = False
            elif key == "fatture_fornitori":
                # Date filter (col 2)
                item_date = table.item(i, 2)
                if item_date:
                    date_val = item_date.data(Qt.UserRole + 1)
                    if date_val:
                        qdate = QDate(date_val.year, date_val.month, date_val.day)
                        if qdate < d_start or qdate > d_end:
                            adv_match = False
                # Esclusione servizi (col 4 = Fornitore)
                servizio_match = False
                if escludi_servizi and adv_match:
                    item_forn = table.item(i, 4)
                    if item_forn:
                        nome_forn = item_forn.text().upper()
                        servizio_match = any(s in nome_forn for s in lista_esclusione)

                # Accumula totali (col 6 = Totale)
                item_totale = table.item(i, 6)
                riga_totale = 0.0
                if item_totale:
                    raw = item_totale.data(Qt.UserRole + 1)
                    riga_totale = raw if raw is not None else 0.0
                count_completo += 1
                totale_completo += riga_totale

                visible = text_match and adv_match and not servizio_match
                table.setRowHidden(i, not visible)
                if visible:
                    count_visibile += 1
                    totale_visibile += riga_totale
                continue

            table.setRowHidden(i, not (text_match and adv_match))

        # Aggiorna barra totali fatture_fornitori
        if key == "fatture_fornitori":
            lbl_vis = self.findChild(QLabel, "lbl_totals_visible_ff")
            lbl_comp = self.findChild(QLabel, "lbl_totals_complete_ff")
            if lbl_vis:
                lbl_vis.setText(f"Visibili: {count_visibile} fatture — € {totale_visibile:,.2f}")
            if lbl_comp:
                lbl_comp.setText(f"Vista completa: {count_completo} fatture — € {totale_completo:,.2f}")

    def run_import(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona File Excel", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            from data_manager import DataManager
            dm = DataManager(self.db_manager)
            try:
                dm.import_all(file_path)
                QMessageBox.information(self, "Successo", "Dati importati con successo!")
                self.load_stats()
                self.switch_view(0)
            except Exception as e:
                QMessageBox.critical(self, "Errore", str(e))
                self.statusBar.showMessage("Errore importazione")

    def show_detail_window(self, window_id, dialog_class, *args):
        """Manage and show detail windows, preventing duplicates."""
        if window_id in self.detail_windows:
            win = self.detail_windows[window_id]
            try:
                win.show()
                win.raise_()
                win.activateWindow()
                return win
            except:
                del self.detail_windows[window_id]
        
        win = dialog_class(*args, parent=self)
        win.setAttribute(Qt.WA_DeleteOnClose)
        win.window_id = window_id
        self.detail_windows[window_id] = win
        win.show()
        win.raise_()
        win.activateWindow()
        return win

    def remove_detail_window(self, window_id):
        """Remove a window from the registry when closed."""
        if window_id in self.detail_windows:
            del self.detail_windows[window_id]

    def open_client_by_code(self, code, name=None):
        if not code and not name: return
        session = self.db_manager.get_session()
        try:
            cliente = None
            if code:
                cliente = session.query(Cliente).filter_by(codice=code).first()
            
            if not cliente and code and code.isdigit():
                for length in [5, 6]:
                    padded = code.zfill(length)
                    cliente = session.query(Cliente).filter_by(codice=padded).first()
                    if cliente: break
            
            if not cliente and name:
                cliente = session.query(Cliente).filter_by(ragione_sociale=name).first()
            
            if not cliente and name:
                cliente = session.query(Cliente).filter(Cliente.ragione_sociale.ilike(f"%{name}%")).first()

            if cliente:
                self.show_detail_window(f"client_{cliente.id}", ClientDetailDialog, cliente)
            else:
                msg = f"Cliente con codice '{code}'"
                if name: msg += f" o nome '{name}'"
                QMessageBox.warning(self, "Attenzione", f"{msg} non trovato nell'anagrafica.")
        finally:
            session.close()

    def handle_client_table_click(self, row, col):
        table = self.sender()
        header = table.horizontalHeaderItem(col).text()
        if header == "Azioni":
            cli_id = None
            for c in range(table.columnCount()):
                item = table.item(row, c)
                if item and item.data(Qt.UserRole) is not None:
                    cli_id = item.data(Qt.UserRole)
                    break
            if cli_id:
                session = self.db_manager.get_session()
                cliente = session.get(Cliente, cli_id)
                if cliente:
                    self.open_invoices_by_client(cliente.codice, cliente.ragione_sociale)
                session.close()

    def handle_article_table_click(self, row, col):
        table = self.sender()
        header = table.horizontalHeaderItem(col).text()
        if header == "Azioni":
            self.open_article_detail(row, col)

    def handle_invoice_table_click(self, row, col):
        table = self.sender()
        header = table.horizontalHeaderItem(col).text()
        if header == "Azioni":
            # Determine if it's a client or supplier action
            action_text = table.item(row, col).text()
            
            code = None
            name = None
            for c in range(table.columnCount()):
                h_text = table.horizontalHeaderItem(c).text()
                if h_text in ["Codice Cliente", "Codice Forn."]:
                    code = table.item(row, c).text()
                elif h_text in ["Cliente", "Fornitore"]:
                    name = table.item(row, c).text()
                    
            if action_text == "👤 Cliente":
                if code or name:
                    self.open_client_by_code(code, name)
            elif action_text == "📦 Fornitore":
                if code or name:
                    self.open_supplier_by_code(code, name)

    def open_supplier_by_code(self, code, name=None):
        """Cerca un fornitore per codice o nome e apre il dettaglio."""
        session = self.db_manager.get_session()
        try:
            supplier = None
            if code:
                supplier = session.query(Fornitore).filter_by(codice=code).first()
            if not supplier and name:
                supplier = session.query(Fornitore).filter_by(ragione_sociale=name).first()
            if not supplier and name:
                supplier = session.query(Fornitore).filter(Fornitore.ragione_sociale.ilike(f"%{name}%")).first()

            if supplier:
                self.show_detail_window(f"supplier_{supplier.id}", SupplierDetailDialog, supplier)
            else:
                QMessageBox.warning(self, "Attenzione", f"Fornitore '{code or name}' non trovato.")
        finally:
            session.close()

    def open_invoices_by_client(self, code, name=None):
        if not code and not name: return
        session = self.db_manager.get_session()
        try:
            from sqlalchemy import or_
            candidate_codes = set()
            if code:
                candidate_codes.add(code)
                candidate_codes.add(code.lstrip('0'))
                if code.isdigit():
                    candidate_codes.add(code.zfill(5))
                    candidate_codes.add(code.zfill(6))
            
            query = session.query(Fattura)
            filters = []
            if candidate_codes:
                filters.append(Fattura.cliente_codice.in_(list(candidate_codes)))
            if name:
                filters.append(Fattura.cliente_denominazione == name)
                filters.append(Fattura.cliente_denominazione.ilike(f"%{name}%"))
            
            invoices = query.filter(or_(*filters)).order_by(Fattura.data.desc()).all()
            
            if not invoices:
                display_name = name or code
                QMessageBox.information(self, "Informazione", f"Nessuna fattura trovata per il cliente: {display_name}")
                return
            
            cliente = None
            if code:
                cliente = session.query(Cliente).filter_by(codice=code).first()
            if not cliente and name:
                cliente = session.query(Cliente).filter_by(ragione_sociale=name).first()

            self.show_detail_window(f"invoices_client_{code or name}", ClientInvoicesDialog, cliente, invoices)
        finally:
            session.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Preferences Setup
    prefs = load_column_prefs()
    
    # Default DB Setup
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_db_path = os.path.join(base_dir, "tebo.db")
    
    # Use saved DB path if it exists, otherwise default
    db_path = prefs.get("db_path", default_db_path)
    
    if not os.path.exists(db_path):
        if os.path.exists(default_db_path):
            db_path = default_db_path
        else:
            print(f"Warning: DB not found at {db_path}. It will be created on import.")

    db_man = DatabaseManager(db_path)
    
    window = MainWindow(db_man)
    window.show()
    sys.exit(app.exec())
