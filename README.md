# HDTV GUI Prototype (Python Standalone)

Ein moderner Viewer für ROOT-Histogramme, basierend auf Python (`PyQt5`, `Uproot`, `Matplotlib`, `Scipy`). Dieses Tool ermöglicht eine native, plattformunabhängige Analyse von ROOT-Dateien ohne die Abhängigkeit von lokalen C++ ROOT-Installationen oder X11-Forwarding.

---

## Funktionsumfang

### 1. Visualisierung und Navigation
* **Universal-Import:** Laden von `.root` Dateien über einen nativen System-Dialog.
* **Struktur-Browser:** Navigation durch Ordnerstrukturen innerhalb der ROOT-Datei (TDirectory).
* **Intelligente Filter:** Automatische Identifikation und Anzeige von `TH1` und `TH2` Objekten.
* **Koordinaten-Anzeige:** Echtzeit-Anzeige der x/y-Werte bei Mausbewegung über dem Spektrum.

### 2. Analyse-Funktionen
* **Gauß-Fits:** Integrierte Peak-Analyse mittels `scipy.optimize`. Berechnet Position (Mean), Breite (Sigma) und Amplitude für den aktuell gewählten Zoom-Bereich.
* **TH2 Projektionen:** Interaktive Erzeugung von 1D-Schnitten aus 2D-Matrizen durch das Setzen von Markern direkt im Plot.
* **Skalierung:** Flexible Umschaltung zwischen linearer und symmetrisch-logarithmischer (SymLog) Darstellung.

### 3. Interaktivität
* **Dynamischer Zoom:** Zentriertes Zoomen auf den Mauszeiger via Mausrad oder Trackpad.
* **Hotkey-Steuerung:** Optimierter Workflow durch Tastaturkurzbefehle für alle Hauptfunktionen.
* **Automatisches Fokus-Management:** Verbesserte Reaktionsfähigkeit der Steuerung auf verschiedenen Betriebssystemen (macOS, Windows, Linux).

---

## Hotkeys

| Taste | Funktion |
| :--- | :--- |
| **F** | Führt einen Gauß-Fit im aktuell sichtbaren Bereich aus. |
| **L** | Schaltet zwischen linearer und SymLog-Skala um. |
| **G** | Blendet das Koordinatengitter ein oder aus. |
| **C / Backspace** | Löscht aktive Fits/Marker und setzt die Ansicht zurück. |

---

## Systemanforderungen

Das Tool läuft rein auf Python-Basis. Ein installiertes C++ ROOT Framework ist nicht erforderlich.

* **Python Version:** 3.x
* **Bibliotheken:** `PyQt5`, `uproot`, `matplotlib`, `mplhep`, `numpy`, `scipy`

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
