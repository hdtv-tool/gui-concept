import sys
import uproot
import mplhep as hep
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

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
from PyQt5.QtCore import Qt

# --- STYLING ---
try:
    hep.style.use("CMS")
except Exception:
    pass

class MainWindow(QMainWindow):
    SUPPORTED_TYPES = ("TH1", "TH2")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HDTV GUI Prototype – Mac Zoom Fixed")
        self.resize(1100, 800)

        # State Variables
        self.root_file = None
        self.cut_points = []
        self.cut_min_bin = None
        self.cut_max_bin = None
        
        # Cache für Analyse-Daten
        self.current_x = None
        self.current_y = None

        # ===================== UI SETUP =====================
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)
        self.setCentralWidget(self.widget)

        # File Handling
        self.btn_load = QPushButton("Load ROOT File")
        self.btn_load.clicked.connect(self.load_file_dialog)
        self.layout.addWidget(self.btn_load)

        self.lbl_status = QLabel("No file loaded.")
        self.layout.addWidget(self.lbl_status)

        # Selectors
        self.layout.addWidget(QLabel("Folder:"))
        self.combo_folder = QComboBox()
        self.combo_folder.currentIndexChanged.connect(self.on_folder_change)
        self.layout.addWidget(self.combo_folder)

        self.layout.addWidget(QLabel("Histogram:"))
        self.combo_hist = QComboBox()
        self.combo_hist.currentIndexChanged.connect(self.on_hist_change)
        self.layout.addWidget(self.combo_hist)

        # Plotting Area
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        # --- FIX FÜR MAC ZOOM ---
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()
        # ------------------------

        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)

        # Controls
        controls = QHBoxLayout()

        self.chk_log = QCheckBox("SymLog Y (L)")
        self.chk_log.stateChanged.connect(self.update_plot_style)
        controls.addWidget(self.chk_log)

        self.chk_grid = QCheckBox("Grid (G)")
        self.chk_grid.stateChanged.connect(self.update_plot_style)
        controls.addWidget(self.chk_grid)

        self.chk_projection = QCheckBox("TH2 Projection")
        self.chk_projection.stateChanged.connect(self.on_hist_change)
        controls.addWidget(self.chk_projection)

        self.combo_proj_axis = QComboBox()
        self.combo_proj_axis.addItems(["X", "Y"])
        self.combo_proj_axis.currentIndexChanged.connect(self.on_hist_change)
        controls.addWidget(self.combo_proj_axis)

        # Fit Button
        self.btn_fit = QPushButton("Fit Gaussian (F)")
        self.btn_fit.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.btn_fit.clicked.connect(self.fit_gaussian)
        controls.addWidget(self.btn_fit)

        self.layout.addLayout(controls)

        # Results & Coords
        self.lbl_fit_result = QLabel("Fit Result: -")
        self.lbl_fit_result.setStyleSheet("color: #c0392b; font-weight: bold;")
        self.layout.addWidget(self.lbl_fit_result)

        self.lbl_coords = QLabel("x: –, y: –")
        self.layout.addWidget(self.lbl_coords)

        # Events
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.canvas.mpl_connect("button_press_event", self.on_click)
        
        # Sicherstellen, dass Hotkeys auch auf Fenster-Ebene gehen
        self.setFocusPolicy(Qt.StrongFocus)

    # ===================== HOTKEYS =====================
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_L:
            self.chk_log.setChecked(not self.chk_log.isChecked())
        elif event.key() == Qt.Key_G:
            self.chk_grid.setChecked(not self.chk_grid.isChecked())
        elif event.key() == Qt.Key_F:
            self.fit_gaussian()
        elif event.key() == Qt.Key_C or event.key() == Qt.Key_Backspace:
            self.on_hist_change()

    # ===================== NAVIGATION =====================
    def load_file_dialog(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Open ROOT File", "", "ROOT Files (*.root)")
        if fn:
            try:
                self.root_file = uproot.open(fn)
                self.lbl_status.setText(f"Loaded: {fn}")
                self.populate_folders()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def populate_folders(self):
        self.combo_folder.clear()
        keys = sorted({k.split(";")[0] for k in self.root_file.keys()})
        self.combo_folder.addItems(keys)
        if keys: self.on_folder_change()

    def on_folder_change(self):
        if not self.root_file: return
        self.combo_hist.clear()
        name = self.combo_folder.currentText()
        try:
            obj = self.root_file[name]
            items = sorted({k.split(";")[0] for k in obj.keys()}) if hasattr(obj, "keys") else [name]
            self.combo_hist.addItems(items)
        except: return
        if self.combo_hist.count() > 0: self.on_hist_change()

    def on_hist_change(self):
        if not self.root_file: return
        folder, hist = self.combo_folder.currentText(), self.combo_hist.currentText()
        path = hist if folder == hist else f"{folder}/{hist}"
        try:
            self.current_x, self.current_y = None, None
            self.lbl_fit_result.setText("Fit Result: -")
            self.plot_object(self.root_file[path], hist)
        except Exception as e: print(e)

    # ===================== PLOT & ANALYSIS =====================
    def plot_object(self, obj, title):
        if not hasattr(obj, "classname") or not obj.classname.startswith(self.SUPPORTED_TYPES): return
        
        self.ax.clear()
        self.ax.set_title(title)

        if obj.classname.startswith("TH1"):
            hep.histplot(obj, ax=self.ax)
            self.current_x, self.current_y = obj.axes[0].centers(), obj.values()
        
        elif obj.classname.startswith("TH2"):
            if self.chk_projection.isChecked():
                axis = self.combo_proj_axis.currentText().lower()
                centers, proj = self.project_th2(obj, axis, self.cut_min_bin, self.cut_max_bin)
                self.ax.plot(centers, proj, drawstyle="steps-mid", color="red", label="Projection")
                self.ax.legend()
                self.current_x, self.current_y = centers, proj
            else:
                v, e0, e1 = obj.values(), obj.axes[0].edges(), obj.axes[1].edges()
                self.ax.imshow(v.T, origin="lower", extent=[e0[0], e0[-1], e1[0], e1[-1]], aspect="auto", cmap="viridis")

        self.update_plot_style()

    def update_plot_style(self):
        self.ax.set_yscale("symlog" if self.chk_log.isChecked() else "linear")
        self.ax.grid(self.chk_grid.isChecked())
        self.canvas.draw_idle()

    def project_th2(self, obj, axis, min_bin, max_bin):
        v = obj.values()
        if axis == "x":
            lo, hi = (0 if min_bin is None else min_bin), (v.shape[1] if max_bin is None else max_bin)
            proj, edges = np.sum(v[:, lo:hi], axis=1), obj.axes[0].edges()
        else:
            lo, hi = (0 if min_bin is None else min_bin), (v.shape[0] if max_bin is None else max_bin)
            proj, edges = np.sum(v[lo:hi, :], axis=0), obj.axes[1].edges()
        return 0.5 * (edges[:-1] + edges[1:]), proj

    def fit_gaussian(self):
        if self.current_x is None: return
        x_min, x_max = self.ax.get_xlim()
        mask = (self.current_x >= x_min) & (self.current_x <= x_max)
        xf, yf = self.current_x[mask], self.current_y[mask]
        if len(xf) < 5: return
        
        def g(x, a, x0, s): return a * np.exp(-(x-x0)**2/(2*s**2))
        try:
            p, _ = curve_fit(g, xf, yf, p0=[np.max(yf), np.mean(xf), (x_max-x_min)/4])
            xd = np.linspace(x_min, x_max, 200)
            self.ax.plot(xd, g(xd, *p), color='red', lw=2, label='Gauss Fit')
            self.ax.legend()
            self.lbl_fit_result.setText(f"Pos: {p[1]:.2f} | Sigma: {p[2]:.2f} | Amp: {p[0]:.0f}")
            self.canvas.draw_idle()
        except Exception as e: QMessageBox.warning(self, "Fit Error", str(e))

    # ===================== INTERACTIVITY =====================
    def on_mouse_move(self, event):
        if event.inaxes: self.lbl_coords.setText(f"x: {event.xdata:.2f}, y: {event.ydata:.2f}")

    def on_scroll(self, event):
        if not event.inaxes: return
        scale = 1/1.2 if event.button == "up" else 1.2
        x0, x1 = self.ax.get_xlim()
        cx = event.xdata
        self.ax.set_xlim(cx - (x1-x0)*scale/2, cx + (x1-x0)*scale/2)
        self.canvas.draw_idle()

    def on_click(self, event):
        # --- FIX FÜR MAC ZOOM (Klick holt Fokus) ---
        self.canvas.setFocus()
        # -------------------------------------------
        
        if self.toolbar.mode or not event.inaxes or event.button != 1 or not self.chk_projection.isChecked(): return
        axis = self.combo_proj_axis.currentText().lower()
        obj = self.root_file[self.combo_folder.currentText() + "/" + self.combo_hist.currentText()]
        if axis == "x":
            self.ax.axhline(event.ydata, color="orange", ls="--")
            val, edges = event.ydata, obj.axes[1].edges()
        else:
            self.ax.axvline(event.xdata, color="orange", ls="--")
            val, edges = event.xdata, obj.axes[0].edges()
        self.cut_points.append(val)
        if len(self.cut_points) == 2:
            v0, v1 = sorted(self.cut_points)
            self.cut_min_bin = np.clip(np.searchsorted(edges, v0)-1, 0, len(edges)-2)
            self.cut_max_bin = np.clip(np.searchsorted(edges, v1)-1, 0, len(edges)-2)
            self.cut_points.clear()
            self.on_hist_change()
        self.canvas.draw_idle()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())