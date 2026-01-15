import sys
import uproot
import mplhep as hep
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HDTV GUI Prototype – Python Only")
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

        # --- Matplotlib Figure + Canvas ---
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
        obj = self.root_file[folder_name]

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
        self.ax.clear()

        if obj.classname.startswith("TH1"):
            hep.histplot(obj, ax=self.ax)
            self.ax.set_ylabel("Counts")

        elif obj.classname.startswith("TH2"):
            values = obj.values()
            x_edges = obj.axes[0].edges()
            y_edges = obj.axes[1].edges()

            self.ax.imshow(
                values.T,
                origin="lower",
                extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]],
                aspect="auto",
                cmap="viridis",
            )

        self.ax.set_title(title)
        self.canvas.draw_idle()

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
