"""
ui/highlights_panel.py
Panel que muestra los highlights detectados por la IA
y permite agregarlos a la lista de clips con un clic.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from core.highlight_detector import Highlight


def secs_to_tc(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:05.2f}"


class HighlightCard(QWidget):
    """Tarjeta visual para un highlight detectado."""
    add_requested  = pyqtSignal(object)   # emite Highlight
    seek_requested = pyqtSignal(float)    # emite segundo

    COLORS = {
        "combinado":  "#ff6b35",
        "reacción":   "#a78bfa",
        "movimiento": "#00e5ff",
        "audio":      "#00c853",
    }

    def __init__(self, highlight: Highlight, parent=None):
        super().__init__(parent)
        self.highlight = highlight
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
            }
            QWidget:hover { border-color: #3a3a3a; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Barra de color lateral según tipo
        color = self.COLORS.get(self.highlight.reason, "#666666")
        bar = QFrame()
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background-color: {color}; border-radius: 2px; border: none;")
        layout.addWidget(bar)

        # Info del highlight
        info = QVBoxLayout()
        info.setSpacing(2)

        label = QLabel(self.highlight.label())
        label.setStyleSheet("color: #dddddd; font-size: 12px; font-weight: 700; border: none; background: transparent;")
        info.addWidget(label)

        times = QLabel(f"{secs_to_tc(self.highlight.start_sec)}  →  {secs_to_tc(self.highlight.end_sec)}  ({self.highlight.duration:.0f}s)")
        times.setStyleSheet("color: #666666; font-size: 11px; font-family: 'Courier New'; border: none; background: transparent;")
        info.addWidget(times)

        # Barra de puntuación
        score_bar = QProgressBar()
        score_bar.setRange(0, 100)
        score_bar.setValue(self.highlight.score_pct)
        score_bar.setTextVisible(False)
        score_bar.setFixedHeight(3)
        score_bar.setStyleSheet(f"""
            QProgressBar {{ background: #2a2a2a; border: none; border-radius: 2px; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}
        """)
        info.addWidget(score_bar)

        layout.addLayout(info, stretch=1)

        # Botones
        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)

        btn_preview = QPushButton("▶")
        btn_preview.setFixedSize(28, 28)
        btn_preview.setToolTip("Previsualizar este momento")
        btn_preview.setStyleSheet("""
            QPushButton { background:#252525; color:#aaaaaa; border:1px solid #333; border-radius:14px; font-size:11px; }
            QPushButton:hover { color:#ffffff; border-color:#555; }
        """)
        btn_preview.clicked.connect(lambda: self.seek_requested.emit(self.highlight.start_sec))
        btn_col.addWidget(btn_preview)

        btn_add = QPushButton("＋")
        btn_add.setFixedSize(28, 28)
        btn_add.setToolTip("Agregar a la lista de clips")
        btn_add.setStyleSheet(f"""
            QPushButton {{ background:#1a2a1a; color:{color}; border:1px solid #2a3a2a; border-radius:14px; font-size:14px; font-weight:700; }}
            QPushButton:hover {{ background:#223322; border-color:{color}; }}
        """)
        btn_add.clicked.connect(lambda: self.add_requested.emit(self.highlight))
        btn_col.addWidget(btn_add)

        layout.addLayout(btn_col)


class HighlightsPanel(QWidget):
    """
    Panel completo de highlights con botón de análisis,
    progreso y lista de resultados.
    """
    highlight_seek    = pyqtSignal(float)    # ir a ese segundo
    highlight_add     = pyqtSignal(object)   # agregar Highlight como clip
    analysis_started  = pyqtSignal()
    analysis_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self._detector = None

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──
        header = QWidget()
        header.setStyleSheet("background:#111111; border-bottom:1px solid #222;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 10, 14, 10)

        title = QLabel("🤖  HIGHLIGHTS IA")
        title.setStyleSheet("font-size:11px; font-weight:700; letter-spacing:2px; color:#555555;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        self._btn_analyze = QPushButton("🔍  Analizar Stream")
        self._btn_analyze.setEnabled(False)
        self._btn_analyze.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2a1a4a,stop:1 #3a2a6a);
                color: #a78bfa; border: 1px solid #4a3a8a;
                border-radius: 6px; padding: 6px 14px;
                font-size: 12px; font-weight: 700;
            }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #3a2a6a,stop:1 #5a3aaa); }
            QPushButton:disabled { background:#1a1a1a; color:#444; border-color:#222; }
        """)
        self._btn_analyze.clicked.connect(self._start_analysis)
        h_layout.addWidget(self._btn_analyze)

        layout.addWidget(header)

        # ── Progreso ──
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(3)
        self._progress.setStyleSheet("""
            QProgressBar { background:#111; border:none; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7c4dff,stop:1 #00e5ff); }
        """)
        layout.addWidget(self._progress)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color:#555; font-size:11px; padding:4px 14px;")
        layout.addWidget(self._status_lbl)

        # ── Lista de highlights ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:#151515; }")

        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet("background:#151515;")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(10, 10, 10, 10)
        self._cards_layout.setSpacing(6)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_widget)
        layout.addWidget(scroll, stretch=1)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def set_ready(self, enabled: bool):
        self._btn_analyze.setEnabled(enabled)

    def set_detector(self, detector):
        self._detector = detector
        self._detector.progress.connect(self._on_progress)
        self._detector.finished.connect(self._on_finished)
        self._detector.error.connect(self._on_error)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _start_analysis(self):
        if not self._detector:
            return
        # Limpiar resultados anteriores
        for i in reversed(range(self._cards_layout.count() - 1)):
            w = self._cards_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        self._btn_analyze.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._status_lbl.setText("Iniciando análisis…")
        self.analysis_started.emit()
        self._detector.start()

    def _on_progress(self, pct: int, msg: str):
        self._progress.setValue(pct)
        self._status_lbl.setText(msg)

    def _on_finished(self, highlights: list):
        self._progress.setValue(100)
        self._btn_analyze.setEnabled(True)

        if not highlights:
            self._status_lbl.setText("No se encontraron highlights destacados.")
            return

        self._status_lbl.setText(f"✓ {len(highlights)} highlights encontrados — haz clic en ＋ para agregar")

        # Insertar tarjetas antes del stretch
        for h in highlights:
            card = HighlightCard(h)
            card.seek_requested.connect(self.highlight_seek)
            card.add_requested.connect(self.highlight_add)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

        self.analysis_finished.emit()

    def _on_error(self, msg: str):
        self._progress.setVisible(False)
        self._btn_analyze.setEnabled(True)
        self._status_lbl.setText(f"⚠ {msg}")
