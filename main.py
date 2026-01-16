import sys
import uproot
import mplhep as hep
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QComboBox, QLabel, QPushButton, QFileDialog, QMessageBox
)

try:
    hep.style.use("CMS")
except Exception:
    pass


class MainWindow(QMainWindow):
    # Define supported ROOT classes for strict type filtering.
    SUPPORTED_TYPES = ("TH1", "TH2")
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HDTV GUI Prototype - Python Only")
        self.resize(1000, 700)
        self.root_file = None

        # --- Main Layout ---
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        # --- File Loading ---
        self.btn_load = QPushButton("Load ROOT File")
        self.btn_load.clicked.connect(self.load_file_dialog)
        self.layout.addWidget(self.btn_load)

        self.lbl_status = QLabel("No file loaded.")
        self.layout.addWidget(self.lbl_status)

        # --- Folder Selector ---
        self.layout.addWidget(QLabel("Folder:"))
        self.combo_folder = QComboBox()
        self.combo_folder.currentIndexChanged.connect(self.on_folder_change)
        self.layout.addWidget(self.combo_folder)

        # --- Histogram Selector ---
        self.layout.addWidget(QLabel("Histogram:"))
        self.combo_hist = QComboBox()
        self.combo_hist.currentIndexChanged.connect(self.on_hist_change)
        self.layout.addWidget(self.combo_hist)

        # --- Matplotlib Integration(Figure + Canvas) ---
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        # >>> NEW: Matplotlib Toolbar (Zoom / Pan / Reset)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)

        #  NEW: Mouse coordinate display
        self.lbl_coords = QLabel("x: –, y: –")
        self.layout.addWidget(self.lbl_coords)

        #  NEW: Matplotlib event connections
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas.mpl_connect("scroll_event", self.on_scroll)

        # NEW: Connect click event
        self.canvas.mpl_connect("button_press_event", self.on_click)

    # ------------------------------------------------------------------

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

    def populate_folders(self):
        self.combo_folder.blockSignals(True)
        self.combo_folder.clear()
        keys = sorted({k.split(";")[0] for k in self.root_file.keys()})
        self.combo_folder.addItems(keys)
        self.combo_folder.blockSignals(False)

        if keys:
            self.on_folder_change()

    def on_folder_change(self):
        if not self.root_file:
            return

        folder_name = self.combo_folder.currentText()
        # Safety check: Handle cases where the folder object cannot be retrieved
        try:
            obj = self.root_file[folder_name]
        except Exception:
            return

        self.combo_hist.blockSignals(True)
        self.combo_hist.clear()

        if hasattr(obj, "keys"):
            hist_items = sorted({k.split(";")[0] for k in obj.keys()})
        elif hasattr(obj, "classname") and obj.classname.startswith("TH"):
            hist_items = [folder_name]
        else:
            hist_items = []

        self.combo_hist.addItems(hist_items)
        self.combo_hist.blockSignals(False)

        if hist_items:
            self.on_hist_change()

    def on_hist_change(self):
        if not self.root_file:
            return

        folder = self.combo_folder.currentText()
        hist = self.combo_hist.currentText()
        path = hist if folder == hist else f"{folder}/{hist}"

        try:
            self.plot_object(self.root_file[path], hist)
        except Exception as e:
            print(f"Error reading object: {e}")

    def plot_object(self, obj, title):
        """
        Central control function for plotting.
        Decides which sub-function to use based on the object type.
        """
        # 1. Check: Ensure the object type is supported
        if not hasattr(obj, "classname") or not obj.classname.startswith(self.SUPPORTED_TYPES):
            print(f"Ignored unsupported object: {getattr(obj, 'classname', 'Unknown')}")
            return

        # Prepare Canvas
        self.ax.clear()
        self.ax.set_title(title)

        # 2. Dispatch logic
        if obj.classname.startswith("TH1"):
            self._plot_th1(obj)
        elif obj.classname.startswith("TH2"):
            self._plot_th2(obj)
        
        # 3. Final Draw(once at the end)
        self.canvas.draw_idle()

    def _plot_th1(self, obj):
        """Rendering logic specific for 1D Histograms."""
        hep.histplot(obj, ax=self.ax)
        self.ax.set_ylabel("Counts")
        # optional: self.ax.set_yscale("log")

    def _plot_th2(self, obj):
        """Rendering logic specific for 2D Histograms (Heatmaps)."""
        values = obj.values()
        x_edges = obj.axes[0].edges()
        y_edges = obj.axes[1].edges()

        # 'aspect="auto"' ensures the heatmap stretches to fill the canvas correctly
        self.ax.imshow(
            values.T,
            origin="lower",
            extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]],
            aspect="auto",
            cmap="viridis",
            interpolation="nearest"
        )

    # ------------------------------------------------------------------
    # FIT API (Technical Preparation)
    # These methods are intended for external calls by the Fit module.
    # ------------------------------------------------------------------

    def add_fit_curve(self, x_data, y_data, color="red", label="Fit"):
        """Overlays a fit curve on the current plot without clearing the canvas."""
        self.ax.plot(x_data, y_data, color=color, linewidth=2, label=label)
        self.ax.legend()
        self.canvas.draw_idle()

    def add_marker(self, x, y, symbol="x", color="black"):
        """Overlays a marker at a specific coordinate (e.g., for peak finding)."""
        self.ax.scatter([x], [y], marker=symbol, color=color, s=100, zorder=10)
        self.canvas.draw_idle()

    def clear_overlays(self):
        """Refreshes the plot to remove overlays."""
        self.on_hist_change()

    # ------------------------------------------------------------------
    #  NEW: Interactivity
    # ------------------------------------------------------------------

    def on_mouse_move(self, event):
        if event.inaxes:
            self.lbl_coords.setText(
                f"x: {event.xdata:.2f}, y: {event.ydata:.2f}"
            )
        else:
            self.lbl_coords.setText("x: –, y: –")

    def on_scroll(self, event):
        if not event.inaxes:
            return

        base_scale = 1.2
        scale = 1 / base_scale if event.button == "up" else base_scale

        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()

        x_range = (x_max - x_min) * scale
        y_range = (y_max - y_min) * scale

        x_center = event.xdata
        y_center = event.ydata

        self.ax.set_xlim(x_center - x_range / 2, x_center + x_range / 2)
        self.ax.set_ylim(y_center - y_range / 2, y_center + y_range / 2)

        self.canvas.draw_idle()

    def on_click(self, event):
        if self.toolbar.mode != "":
            return
        if not event.inaxes: return
        if event.button != 1: return
        self.add_marker(event.xdata, event.ydata)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
