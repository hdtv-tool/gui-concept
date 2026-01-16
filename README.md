# gui-concept
Frontend purely in python

https://www.desy.de/~tadej/tutorial/

# HDTV GUI Prototype (Python Standalone)

Ein leichtgewichtiger Viewer für ROOT-Histogramme, basierend auf Python (`PyQt5`, `Uproot`, `Matplotlib`).
Dieses Tool ersetzt die Abhängigkeit von X11-Forwarding und lokalen C++ ROOT-Installationen durch eine native, plattformunabhängige Lösung.

---

## Funktionsumfang

### 1. Datei-Handling & Navigation
* **Universal-Import:** Laden beliebiger `.root` Dateien über den nativen System-Dialog.
* **Struktur-Browser:** Effizientes Navigieren durch Ordnerstrukturen (TDirectory).
* **Intelligente Filter:** Zeigt automatisch nur kompatible Objekte (`TH1`, `TH2`) an.
* **Stabilität:** Robuste Fehlerbehandlung bei leeren Ordnern oder unbekannten Dateitypen (keine Abstürze).

### 2. Visualisierung (Plotting)
* **1D-Histogramme (TH1):** Präzise Darstellung als Step-Plot mit korrekten Bins.
* **2D-Matrizen (TH2):** Darstellung als Heatmap (Colorplot) mit modernen Farbschemata (z.B. Viridis).
* **Live-Koordinaten:** Exakte Anzeige der x/y-Werte bei Mausbewegung über dem Plot.

### 3. Interaktivität & Analyse
* **Native Toolbar:** Werkzeuge zum Zoomen (Rechteck), Pannen (Verschieben) und Zurücksetzen der Ansicht.
* **Click-to-Mark:** Interaktives Setzen von Markern per Mausklick zur schnellen Peak-Identifikation.
* **Konflikt-Schutz:** Eine intelligente Logik verhindert das versehentliche Setzen von Markern, während das Zoom-Werkzeug aktiv ist.

### 4. Live-Controls (Darstellungs-Optionen)
* **SymLog Skalierung:** Umschaltbar zwischen Linear und Symmetrisch-Logarithmisch (behandelt Nullen und negative Werte korrekt, im Gegensatz zu einfachem Log).
* **Grid (Gitter):** Ein-/Ausblendbares Raster zur besseren Orientierung im Spektrum.
* **State Persistence:** Benutzereinstellungen (z.B. Log-Skala aktiviert) bleiben erhalten, auch wenn durch verschiedene Histogramme geblättert wird.

---

## 💻 Systemanforderungen

Das Tool benötigt kein installiertes C++ ROOT Framework. Es läuft rein auf Python.

* **Python Version:** 3.x
* **Benötigte Bibliotheken:**
    * `PyQt5` (GUI Framework)
    * `uproot` (I/O für ROOT Dateien)
    * `matplotlib` & `mplhep` (Plotting)
    * `numpy` (Datenverarbeitung)

---

## Installation & Start

#### 1. Virtuelle Umgebung erstellen (optional, aber empfohlen)
python3 -m venv venv

source venv/bin/activate  (Auf Windows: venv\Scripts\activate)

#### 2. Abhängigkeiten installieren
pip install -r requirements.txt

#### 3. Programm starten
python main.py
