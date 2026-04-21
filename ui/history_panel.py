"""
ui/history_panel.py
Panel que muestra el historial de clips exportados por el usuario.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
import os
from datetime import datetime


def fmt_duration(secs: float) -> str:
    m = int(secs // 60)
    s = int(secs % 60)
    return f"{m}:{s:02d}"


def fmt_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return iso


class HistoryPanel(QWidget):
    """Panel de historial de clips exportados."""

    reexport_requested = pyqtSignal(object)   # emite ClipHistory

    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth = auth_manager
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background:#111111; border-bottom:1px solid #222;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(14, 10, 14, 10)

        title = QLabel("📋  HISTORIAL DE CLIPS")
        title.setStyleSheet("font-size:11px; font-weight:700; letter-spacing:2px; color:#555555;")
        h_lay.addWidget(title)
        h_lay.addStretch()

        btn_refresh = QPushButton("↻")
        btn_refresh.setFixedSize(28, 28)
        btn_refresh.setToolTip("Actualizar historial")
        btn_refresh.setStyleSheet("""
            QPushButton { background:#1a1a1a; color:#666; border:1px solid #2a2a2a; border-radius:14px; }
            QPushButton:hover { color:#fff; border-color:#555; }
        """)
        btn_refresh.clicked.connect(self.refresh)
        h_lay.addWidget(btn_refresh)

        layout.addWidget(header)

        # Lista
        self._list = QListWidget()
        self._list.setStyleSheet("""
            QListWidget { background:#111111; border:none; }
            QListWidget::item { 
                background:#151515; border-bottom:1px solid #1a1a1a; 
                padding:10px 14px; color:#cccccc;
            }
            QListWidget::item:selected { background:#1a1a2a; }
            QListWidget::item:hover { background:#1a1a1a; }
        """)
        layout.addWidget(self._list, stretch=1)

        # Botón re-exportar
        self._btn_reexport = QPushButton("⬆  Re-exportar clip seleccionado")
        self._btn_reexport.setEnabled(False)
        self._btn_reexport.setStyleSheet("""
            QPushButton {
                background:#0d1a0d; color:#00c853; border:1px solid #1a3a1a;
                border-radius:0; padding:10px; font-size:12px; font-weight:600;
            }
            QPushButton:hover { background:#112211; }
            QPushButton:disabled { background:#111; color:#333; border-color:#1a1a1a; }
        """)
        self._btn_reexport.clicked.connect(self._on_reexport)
        layout.addWidget(self._btn_reexport)

        self._list.currentRowChanged.connect(
            lambda r: self._btn_reexport.setEnabled(r >= 0)
        )

        self._history_data = []

    def refresh(self):
        self._list.clear()
        self._history_data = self.auth.get_clip_history()

        if not self._history_data:
            item = QListWidgetItem("  Sin clips exportados aún.")
            item.setFlags(Qt.NoItemFlags)
            item.setForeground(Qt.darkGray)
            self._list.addItem(item)
            return

        for clip in self._history_data:
            exists = os.path.exists(clip.output_path)
            status = "✓" if exists else "✗"
            color  = "#00c853" if exists else "#ff5555"
            name   = clip.label or os.path.basename(clip.output_path)
            dur    = fmt_duration(clip.duration)
            date   = fmt_date(clip.created_at)
            text   = f"{status}  {name}\n    ⏱ {dur}  ·  {clip.preset}  ·  {date}"
            item   = QListWidgetItem(text)
            item.setForeground(Qt.white if exists else Qt.darkGray)
            self._list.addItem(item)

    def _on_reexport(self):
        row = self._list.currentRow()
        if 0 <= row < len(self._history_data):
            self.reexport_requested.emit(self._history_data[row])
