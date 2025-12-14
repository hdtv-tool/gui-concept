import sys
import uproot
import mplhep as hep
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QComboBox, QLabel, QPushButton, QFileDialog, QMessageBox
)

# Style setup (optional, falls Fehler auftritt ignorieren)
try:
    hep.style.use("CMS")
except Exception:
    pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HDTV GUI Prototype – Python Only")
        self.resize(1000, 700)
        self.root_file = None

        # --- GUI Setup ---
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        # 1. NEU: Datei-Auswahl-Button (statt festem Pfad)
        self.btn_load = QPushButton("📂 Load ROOT File")
        self.btn_load.clicked.connect(self.load_file_dialog)
        self.layout.addWidget(self.btn_load)
        
        self.lbl_status = QLabel("No file loaded.")
        self.layout.addWidget(self.lbl_status)

        # 2. Dropdowns
        self.layout.addWidget(QLabel("Folder:"))
        self.combo_folder = QComboBox()
        self.combo_folder.currentIndexChanged.connect(self.on_folder_change)
        self.layout.addWidget(self.combo_folder)

        self.layout.addWidget(QLabel("Histogram:"))
        self.combo_hist = QComboBox()
        self.combo_hist.currentIndexChanged.connect(self.on_hist_change)
        self.layout.addWidget(self.combo_hist)

        # 3. Matplotlib Canvas (Saubere Einbettung)
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.layout.addWidget(self.canvas)

    # --- Logik: Datei öffnen ---
    def load_file_dialog(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open ROOT File", "", "ROOT Files (*.root);;All Files (*)"
        )
        if filename:
            try:
                self.root_file = uproot.open(filename)
                self.lbl_status.setText(f"Loaded: {filename}")
                self.populate_folders()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")

    # --- Logik: Ordner füllen ---
    def populate_folders(self):
        self.combo_folder.blockSignals(True)
        self.combo_folder.clear()
        # Keys holen und bereinigen
        keys = sorted(list(set([k.split(";")[0] for k in self.root_file.keys()])))
        self.combo_folder.addItems(keys)
        self.combo_folder.blockSignals(False)
        if keys: self.on_folder_change()

    # --- Logik: Histogramm-Liste füllen ---
    def on_folder_change(self):
        if not self.root_file: return
        folder_name = self.combo_folder.currentText()
        obj = self.root_file[folder_name]
        
        self.combo_hist.blockSignals(True)
        self.combo_hist.clear()
        
        hist_items = []
        # Ist es ein Ordner (TDirectory)?
        if hasattr(obj, "keys"): 
            hist_items = sorted(list(set([k.split(";")[0] for k in obj.keys()])))
        # Ist es direkt ein Histogramm?
        elif hasattr(obj, "classname") and obj.classname.startswith("TH"): 
            hist_items = [folder_name]
            
        self.combo_hist.addItems(hist_items)
        self.combo_hist.blockSignals(False)
        if hist_items: self.on_hist_change()

    # --- Logik: Plotten ---
    def on_hist_change(self):
        if not self.root_file: return
        folder = self.combo_folder.currentText()
        hist = self.combo_hist.currentText()
        
        path = hist if folder == hist else f"{folder}/{hist}"
        try:
            self.plot_object(self.root_file[path], hist)
        except Exception as e:
            print(f"Error reading object: {e}")

    def plot_object(self, obj, title):
        self.ax.clear()
        # Typ prüfen (1D oder 2D)
        if obj.classname.startswith("TH1"):
            hep.histplot(obj, ax=self.ax)
            self.ax.set_ylabel("Counts")
        elif obj.classname.startswith("TH2"):
            values = obj.values()
            x_edges = obj.axes[0].edges()
            y_edges = obj.axes[1].edges()
            self.ax.imshow(values.T, origin='lower', extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]], aspect='auto', cmap='viridis')
        
        self.ax.set_title(title)
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())