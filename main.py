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
    QComboBox, QLabel, QPushButton, QFileDialog,
    QMessageBox, QHBoxLayout, QCheckBox
)

try:
    hep.style.use("CMS")
except Exception:
    pass


class MainWindow(QMainWindow):

    SUPPORTED_TYPES = ("TH1", "TH2")

    def __init__(self):
        super().__init__()

        self.setWindowTitle("HDTV GUI Prototype – Python Only")
        self.resize(1000, 700)

        self.root_file = None

        # Gate / Cut state
        self.cut_points = []
        self.cut_min_bin = None
        self.cut_max_bin = None

        # ===================== UI =====================

        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)
        self.setCentralWidget(self.widget)

        self.btn_load = QPushButton("Load ROOT File")
        self.btn_load.clicked.connect(self.load_file_dialog)
        self.layout.addWidget(self.btn_load)

        self.lbl_status = QLabel("No file loaded.")
        self.layout.addWidget(self.lbl_status)

        self.layout.addWidget(QLabel("Folder:"))
        self.combo_folder = QComboBox()
        self.combo_folder.currentIndexChanged.connect(self.on_folder_change)
        self.layout.addWidget(self.combo_folder)

        self.layout.addWidget(QLabel("Histogram:"))
        self.combo_hist = QComboBox()
        self.combo_hist.currentIndexChanged.connect(self.on_hist_change)
        self.layout.addWidget(self.combo_hist)

        # ===================== Matplotlib =====================

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)

        # ===================== Controls =====================

        controls = QHBoxLayout()

        self.chk_log = QCheckBox("SymLog Y")
        self.chk_log.stateChanged.connect(self.update_plot_style)
        controls.addWidget(self.chk_log)

        self.chk_grid = QCheckBox("Grid")
        self.chk_grid.stateChanged.connect(self.update_plot_style)
        controls.addWidget(self.chk_grid)

        self.chk_projection = QCheckBox("TH2 Projection")
        self.chk_projection.stateChanged.connect(self.on_hist_change)
        controls.addWidget(self.chk_projection)

        controls.addWidget(QLabel("Axis:"))
        self.combo_proj_axis = QComboBox()
        self.combo_proj_axis.addItems(["X", "Y"])
        self.combo_proj_axis.currentIndexChanged.connect(self.on_hist_change)
        controls.addWidget(self.combo_proj_axis)

        self.layout.addLayout(controls)

        self.lbl_coords = QLabel("x: –, y: –")
        self.layout.addWidget(self.lbl_coords)

        # ===================== Events =====================

        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.canvas.mpl_connect("button_press_event", self.on_click)

    # ======================================================
    # File handling
    # ======================================================

    def load_file_dialog(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open ROOT File", "", "ROOT Files (*.root)"
        )
        if not filename:
            return

        try:
            self.root_file = uproot.open(filename)
            self.lbl_status.setText(f"Loaded: {filename}")
            self.populate_folders()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def populate_folders(self):
        self.combo_folder.clear()
        keys = sorted({k.split(";")[0] for k in self.root_file.keys()})
        self.combo_folder.addItems(keys)
        if keys:
            self.on_folder_change()

    def on_folder_change(self):
        if not self.root_file:
            return

        self.combo_hist.clear()
        name = self.combo_folder.currentText()

        try:
            obj = self.root_file[name]
        except Exception:
            return

        if hasattr(obj, "keys"):
            items = sorted({k.split(";")[0] for k in obj.keys()})
        else:
            items = [name]

        self.combo_hist.addItems(items)
        if items:
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
            print(e)

    # ======================================================
    # Plot logic
    # ======================================================

    def plot_object(self, obj, title):
        if not hasattr(obj, "classname"):
            return

        if not obj.classname.startswith(self.SUPPORTED_TYPES):
            return

        self.ax.clear()
        self.ax.set_title(title)

        if obj.classname.startswith("TH1"):
            hep.histplot(obj, ax=self.ax)
            self.ax.set_ylabel("Counts")

        elif obj.classname.startswith("TH2"):
            if self.chk_projection.isChecked():
                axis = self.combo_proj_axis.currentText().lower()
                centers, proj = self.project_th2(
                    obj, axis,
                    self.cut_min_bin,
                    self.cut_max_bin
                )
                self.ax.plot(
                    centers, proj,
                    drawstyle="steps-mid",
                    color="red",
                    label="Projection"
                )
                self.ax.legend()
            else:
                values = obj.values()
                x_edges = obj.axes[0].edges()
                y_edges = obj.axes[1].edges()
                self.ax.imshow(
                    values.T,
                    origin="lower",
                    extent=[x_edges[0], x_edges[-1],
                            y_edges[0], y_edges[-1]],
                    aspect="auto",
                    cmap="viridis"
                )

        self.update_plot_style()

    def update_plot_style(self):
        self.ax.set_yscale("symlog" if self.chk_log.isChecked() else "linear")
        self.ax.grid(self.chk_grid.isChecked())
        self.canvas.draw_idle()

    # ======================================================
    # Projection & Cuts
    # ======================================================

    def project_th2(self, obj, axis, min_bin, max_bin):
        values = obj.values()

        if axis == "x":
            lo = 0 if min_bin is None else min_bin
            hi = values.shape[1] if max_bin is None else max_bin
            proj = np.sum(values[:, lo:hi], axis=1)
            edges = obj.axes[0].edges()
        else:
            lo = 0 if min_bin is None else min_bin
            hi = values.shape[0] if max_bin is None else max_bin
            proj = np.sum(values[lo:hi, :], axis=0)
            edges = obj.axes[1].edges()

        centers = 0.5 * (edges[:-1] + edges[1:])
        return centers, proj

    def find_bin_from_edges(self, edges, value):
        return np.clip(np.searchsorted(edges, value) - 1, 0, len(edges) - 2)

    # ======================================================
    # Interactivity
    # ======================================================

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

        scale = 1 / 1.2 if event.button == "up" else 1.2
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()

        cx, cy = event.xdata, event.ydata
        self.ax.set_xlim(cx - (x1 - x0) * scale / 2,
                         cx + (x1 - x0) * scale / 2)
        self.ax.set_ylim(cy - (y1 - y0) * scale / 2,
                         cy + (y1 - y0) * scale / 2)

        self.canvas.draw_idle()

    def on_click(self, event):
        if self.toolbar.mode or not event.inaxes or event.button != 1:
            return

        if not self.chk_projection.isChecked():
            return

        axis = self.combo_proj_axis.currentText().lower()

        folder = self.combo_folder.currentText()
        hist = self.combo_hist.currentText()
        path = hist if folder == hist else f"{folder}/{hist}"
        obj = self.root_file[path]

        if axis == "x":
            # Gate on Y → horizontal lines
            self.ax.axhline(event.ydata, color="orange", linestyle="--")
            value = event.ydata
            edges = obj.axes[1].edges()
        else:
            # Gate on X → vertical lines
            self.ax.axvline(event.xdata, color="orange", linestyle="--")
            value = event.xdata
            edges = obj.axes[0].edges()

        self.cut_points.append(value)

        if len(self.cut_points) == 2:
            v0, v1 = sorted(self.cut_points)
            self.cut_min_bin = self.find_bin_from_edges(edges, v0)
            self.cut_max_bin = self.find_bin_from_edges(edges, v1)
            self.cut_points.clear()
            self.on_hist_change()

        self.canvas.draw_idle()


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
