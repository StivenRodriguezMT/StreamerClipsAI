"""
ui/clips_panel.py
Left/right panel that lists all created clips.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from core.clip_model import Clip


class ClipListItem(QListWidgetItem):
    def __init__(self, clip: Clip):
        super().__init__()
        self.clip = clip
        self._refresh()

    def _refresh(self):
        name = self.clip.display_name()
        dur = self.clip.duration_str
        preset_short = self.clip.export_preset.split("(")[0].strip()
        self.setText(f"  {name}\n  ⏱ {dur}  ·  {preset_short}")
        self.setToolTip(
            f"Fuente: {self.clip.source_path}\n"
            f"Entrada:  {self.clip.in_seconds:.2f}s\n"
            f"Salida: {self.clip.out_seconds:.2f}s\n"
            f"Duración: {self.clip.duration_str}"
        )


class ClipsPanel(QWidget):
    clip_selected = pyqtSignal(object)   # emits Clip
    clip_deleted = pyqtSignal(object)    # emits Clip

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("clips_panel")
        self.setMinimumWidth(200)
        self.setMaximumWidth(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("CLIPS")
        header.setObjectName("panel_title")
        layout.addWidget(header)

        # Lista
        self._list = QListWidget()
        self._list.setSpacing(2)
        self._list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list)

        # Botón eliminar
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(8, 6, 8, 8)
        self._btn_delete = QPushButton("🗑  Eliminar")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._delete_selected)
        btn_row.addWidget(self._btn_delete)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_clip(self, clip: Clip):
        item = ClipListItem(clip)
        self._list.addItem(item)
        self._list.setCurrentItem(item)

    def update_clip(self, clip: Clip):
        for i in range(self._list.count()):
            item = self._list.item(i)
            if isinstance(item, ClipListItem) and item.clip.id == clip.id:
                item.clip = clip
                item._refresh()
                break

    def all_clips(self):
        clips = []
        for i in range(self._list.count()):
            item = self._list.item(i)
            if isinstance(item, ClipListItem):
                clips.append(item.clip)
        return clips

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_selection_changed(self, current, previous):
        if isinstance(current, ClipListItem):
            self._btn_delete.setEnabled(True)
            self.clip_selected.emit(current.clip)
        else:
            self._btn_delete.setEnabled(False)

    def _delete_selected(self):
        row = self._list.currentRow()
        if row < 0:
            return
        item = self._list.takeItem(row)
        if isinstance(item, ClipListItem):
            self.clip_deleted.emit(item.clip)
