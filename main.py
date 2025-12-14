import sys
import uproot
import mplhep as hep
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QComboBox, QLabel, QPushButton, QFileDialog, QMessageBox
)

# Optional: Apply CMS style if available; fail gracefully if not.
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

        # --- Main Layout Initialization ---
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        # --- File Loading Controls ---
        self.btn_load = QPushButton("Load ROOT File")
        self.btn_load.clicked.connect(self.load_file_dialog)
        self.layout.addWidget(self.btn_load)
        
        self.lbl_status = QLabel("No file loaded.")
        self.layout.addWidget(self.lbl_status)

        # --- Data Selection Controls ---
        self.layout.addWidget(QLabel("Folder:"))
        self.combo_folder = QComboBox()
        self.combo_folder.currentIndexChanged.connect(self.on_folder_change)
        self.layout.addWidget(self.combo_folder)

        self.layout.addWidget(QLabel("Histogram:"))
        self.combo_hist = QComboBox()
        self.combo_hist.currentIndexChanged.connect(self.on_hist_change)
        self.layout.addWidget(self.combo_hist)

        # --- Matplotlib Canvas Integration ---
        # Using Figure() directly is thread-safe and preferred for GUI embedding
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.layout.addWidget(self.canvas)

    def load_file_dialog(self):
        """Opens system file dialog to select a ROOT file."""
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

    def populate_folders(self):
        """Extracts top-level keys from the ROOT file to populate the folder dropdown."""
        self.combo_folder.blockSignals(True)
        self.combo_folder.clear()
        
        # Retrieve keys and remove cycle numbers (e.g., 'name;1' -> 'name')
        keys = sorted(list(set([k.split(";")[0] for k in self.root_file.keys()])))
        
        self.combo_folder.addItems(keys)
        self.combo_folder.blockSignals(False)
        
        if keys: 
            self.on_folder_change()

    def on_folder_change(self):
        """Updates the histogram dropdown based on the selected folder."""
        if not self.root_file: 
            return
            
        folder_name = self.combo_folder.currentText()
        obj = self.root_file[folder_name]
        
        self.combo_hist.blockSignals(True)
        self.combo_hist.clear()
        
        hist_items = []
        
        # Case A: Object is a TDirectory (contains other keys)
        if hasattr(obj, "keys"): 
            hist_items = sorted(list(set([k.split(";")[0] for k in obj.keys()])))
            
        # Case B: Object is a top-level Histogram (TH1/TH2)
        elif hasattr(obj, "classname") and obj.classname.startswith("TH"): 
            hist_items = [folder_name]
            
        self.combo_hist.addItems(hist_items)
        self.combo_hist.blockSignals(False)
        
        if hist_items: 
            self.on_hist_change()

    def on_hist_change(self):
        """Triggered when a histogram is selected; initiates plotting."""
        if not self.root_file: 
            return
            
        folder = self.combo_folder.currentText()
        hist = self.combo_hist.currentText()
        
        # Construct path depending on whether we are in a subdir or root
        path = hist if folder == hist else f"{folder}/{hist}"
        
        try:
            self.plot_object(self.root_file[path], hist)
        except Exception as e:
            print(f"Error reading object: {e}")

    def plot_object(self, obj, title):
        """Clears the canvas and renders the given ROOT object using mplhep."""
        self.ax.clear()
        
        # Handle 1D Histograms
        if obj.classname.startswith("TH1"):
            hep.histplot(obj, ax=self.ax)
            self.ax.set_ylabel("Counts")
            
        # Handle 2D Histograms (Heatmaps)
        elif obj.classname.startswith("TH2"):
            values = obj.values()
            x_edges = obj.axes[0].edges()
            y_edges = obj.axes[1].edges()
            
            self.ax.imshow(
                values.T, 
                origin='lower', 
                extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]], 
                aspect='auto', 
                cmap='viridis'
            )
        
        self.ax.set_title(title)
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())