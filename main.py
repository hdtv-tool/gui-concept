import sys
import uproot
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QComboBox, QLabel
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

hep.style.use("CMS")   # nice HEP styling


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HDTV GUI Prototype – ROOT Browser")

        # --- GUI Framework ---
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        # ROOT FILE PATH (WSL → your file)
        self.root_file_path = "/mnt/c/Users/nasir/hdtv/data/allruns_hists.root"
        self.root_file = uproot.open(self.root_file_path)

        # --- Folder Selector ---
        self.folder_dropdown = QComboBox()
        self.layout.addWidget(QLabel("Select folder:"))
        self.layout.addWidget(self.folder_dropdown)

        # Fill with top-level keys
        folders = [k.split(";")[0] for k in self.root_file.keys()]
        self.folder_dropdown.addItems(folders)

        # --- Histogram Selector ---
        self.hist_dropdown = QComboBox()
        self.layout.addWidget(QLabel("Select histogram:"))
        self.layout.addWidget(self.hist_dropdown)

        # --- Matplotlib Canvas ---
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # --- Connect signals ---
        self.folder_dropdown.currentIndexChanged.connect(self.update_hist_list)
        self.hist_dropdown.currentIndexChanged.connect(self.plot_selected_histogram)

        # Load first folder
        self.update_hist_list()

    # ----------------------------------------------------------------------
    # FIXED: This now safely handles: 
    # - folders (TDirectory)
    # - histograms (TH1 / TH2 objects)
    # ----------------------------------------------------------------------
    def update_hist_list(self):
        folder_name = self.folder_dropdown.currentText()
        folder_obj = self.root_file[folder_name]

        hist_names = []

        # Case 1 → Folder (TDirectory)
        if hasattr(folder_obj, "keys"):
            for key in folder_obj.keys():
                clean = key.split(";")[0]
                hist_names.append(clean)

        # Case 2 → Direct histogram object
        else:
            if hasattr(folder_obj, "classname") and folder_obj.classname.startswith(("TH1", "TH2")):
                hist_names.append(folder_name)

        self.hist_dropdown.clear()
        self.hist_dropdown.addItems(hist_names)

        if hist_names:
            self.plot_selected_histogram(0)

    # ----------------------------------------------------------------------
    # Plotting function
    # ----------------------------------------------------------------------
    def plot_selected_histogram(self, index):
        if index < 0:
            return

        folder_name = self.folder_dropdown.currentText()
        hist_name = self.hist_dropdown.currentText()

        full_path = f"{folder_name}/{hist_name}"
        hist_obj = self.root_file[full_path]

        self.ax.clear()

        # TH2 → heatmap
        if hist_obj.classname.startswith("TH2"):
            x_edges = hist_obj.axes[0].edges()
            y_edges = hist_obj.axes[1].edges()
            values = hist_obj.values()

            self.ax.imshow(
                values.T,
                origin="lower",
                extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]],
                aspect="auto",
                cmap="viridis",
            )
            self.ax.set_title(hist_name)
            self.ax.set_xlabel("X axis")
            self.ax.set_ylabel("Y axis")

        # TH1 → normal histogram
        elif hist_obj.classname.startswith("TH1"):
            values = hist_obj.values()
            edges = hist_obj.axes[0].edges()

            hep.histplot(values, edges, ax=self.ax)
            self.ax.set_title(hist_name)
            self.ax.set_xlabel("X axis")
            self.ax.set_ylabel("Counts")

        else:
            self.ax.text(0.5, 0.5, f"Unsupported: {hist_obj.classname}",
                         ha="center", va="center")

        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
