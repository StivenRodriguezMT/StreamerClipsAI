"""
ui/clip_creator_panel.py
Right panel: set in/out points, choose export format, export clip.
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QProgressBar, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from core.clip_model import Clip
from core.ffmpeg_handler import EXPORT_PRESETS, ExportWorker, find_ffmpeg, seconds_to_hms


def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFrameShadow(QFrame.Sunken)
    return f


class ClipCreatorPanel(QWidget):
    clip_created = pyqtSignal(object)    # emits Clip
    export_started = pyqtSignal()
    export_finished = pyqtSignal(str)    # output path
    export_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("clip_creator_panel")
        self.setMinimumWidth(240)
        self.setMaximumWidth(280)

        self._source_path = ""
        self._fps = 30.0
        self._total_frames = 0
        self._in_frame = -1
        self._out_frame = -1
        self._export_worker = None
        self._ffmpeg_path = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # ---- Title ----
        title = QLabel("CREADOR DE CLIPS")
        title.setObjectName("section_title")
        layout.addWidget(title)

        layout.addWidget(_sep())

        # ---- Timecode ----
        self._timecode = QLabel("00:00:00")
        self._timecode.setObjectName("timecode_label")
        self._timecode.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._timecode)

        # ---- IN / OUT ----
        in_out_row = QHBoxLayout()
        self._btn_in = QPushButton("[ ENTRADA")
        self._btn_in.setObjectName("btn_set_in")
        self._btn_in.setToolTip("Marcar punto de inicio del clip (I)")
        self._btn_in.clicked.connect(self._set_in)
        in_out_row.addWidget(self._btn_in)

        self._btn_out = QPushButton("SALIDA ]")
        self._btn_out.setObjectName("btn_set_out")
        self._btn_out.setToolTip("Marcar punto de fin del clip (O)")
        self._btn_out.clicked.connect(self._set_out)
        in_out_row.addWidget(self._btn_out)
        layout.addLayout(in_out_row)

        # ---- IN / OUT display ----
        self._in_label = QLabel("ENTRADA  —")
        self._in_label.setObjectName("time_display")
        self._out_label = QLabel("SALIDA —")
        self._out_label.setObjectName("time_display")
        layout.addWidget(self._in_label)
        layout.addWidget(self._out_label)

        # ---- Duración ----
        self._dur_label = QLabel("Duración: —")
        self._dur_label.setObjectName("time_display")
        layout.addWidget(self._dur_label)

        layout.addWidget(_sep())

        # ---- Clip label ----
        lbl = QLabel("Nombre del Clip (opcional)")
        lbl.setObjectName("time_display")
        layout.addWidget(lbl)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("ej. Victoria épica #1")
        layout.addWidget(self._name_edit)

        # ---- Export format ----
        fmt_lbl = QLabel("Formato de Exportación")
        fmt_lbl.setObjectName("time_display")
        layout.addWidget(fmt_lbl)

        self._combo_format = QComboBox()
        for key in EXPORT_PRESETS.keys():
            self._combo_format.addItem(key)
        layout.addWidget(self._combo_format)

        layout.addWidget(_sep())

        # ---- Save Clip button ----
        self._btn_save = QPushButton("＋  Agregar a la Lista")
        self._btn_save.setEnabled(False)
        self._btn_save.clicked.connect(self._save_clip)
        layout.addWidget(self._btn_save)

        # ---- Botón exportar ----
        self._btn_export = QPushButton("⬆  Exportar Ahora")
        self._btn_export.setObjectName("btn_export_clip")
        self._btn_export.setEnabled(False)
        self._btn_export.clicked.connect(self._export_clip)
        layout.addWidget(self._btn_export)

        # ---- Progress ----
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        layout.addWidget(self._progress)

        self._status_lbl = QLabel("")
        self._status_lbl.setObjectName("time_display")
        self._status_lbl.setWordWrap(True)
        layout.addWidget(self._status_lbl)

        layout.addStretch()

        # Try to find FFmpeg early
        try:
            self._ffmpeg_path = find_ffmpeg()
        except RuntimeError:
            self._ffmpeg_path = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_source(self, path: str, fps: float, total_frames: int):
        self._source_path = path
        self._fps = fps
        self._total_frames = total_frames
        self._in_frame = -1
        self._out_frame = -1
        self._refresh_display()

    def update_current_frame(self, frame: int):
        secs = frame / self._fps if self._fps else 0
        h = int(secs // 3600)
        m = int((secs % 3600) // 60)
        s = secs % 60
        self._timecode.setText(f"{h:02d}:{m:02d}:{s:05.2f}")
        self._current_frame = frame

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _set_in(self):
        if not hasattr(self, "_current_frame"):
            return
        self._in_frame = self._current_frame
        self._refresh_display()

    def _set_out(self):
        if not hasattr(self, "_current_frame"):
            return
        self._out_frame = self._current_frame
        self._refresh_display()

    def _refresh_display(self):
        def fmt(f):
            if f < 0:
                return "—"
            secs = f / self._fps if self._fps else 0
            return seconds_to_hms(secs)

        self._in_label.setText(f"ENTRADA   {fmt(self._in_frame)}")
        self._out_label.setText(f"SALIDA  {fmt(self._out_frame)}")

        valid = self._in_frame >= 0 and self._out_frame > self._in_frame
        if valid:
            dur = (self._out_frame - self._in_frame) / self._fps
            m = int(dur // 60)
            s = dur % 60
            self._dur_label.setText(f"Duración: {m}:{s:05.2f}")
        else:
            self._dur_label.setText("Duración: —")

        self._btn_save.setEnabled(valid)
        self._btn_export.setEnabled(valid and bool(self._source_path))

    def _build_clip(self) -> Clip:
        label = self._name_edit.text().strip()
        return Clip(
            source_path=self._source_path,
            in_frame=self._in_frame,
            out_frame=self._out_frame,
            fps=self._fps,
            label=label,
            export_preset=self._combo_format.currentText(),
        )

    def _save_clip(self):
        clip = self._build_clip()
        if clip.is_valid():
            self.clip_created.emit(clip)
            self._status_lbl.setText("✓ Clip agregado a la lista.")

    def _export_clip(self):
        if not self._ffmpeg_path:
            try:
                self._ffmpeg_path = find_ffmpeg()
            except RuntimeError as e:
                self.export_error.emit(str(e))
                self._status_lbl.setText("⚠ FFmpeg no encontrado.")
                return

        clip = self._build_clip()
        if not clip.is_valid():
            return

        from PyQt5.QtWidgets import QFileDialog
        preset = EXPORT_PRESETS[clip.export_preset]
        ext = preset["ext"]
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Clip Como", f"clip_{clip.id}.{ext}",
            f"Video (*.{ext})"
        )
        if not save_path:
            return

        self._btn_export.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._status_lbl.setText("Exportando…")

        self._export_worker = ExportWorker(
            ffmpeg_path=self._ffmpeg_path,
            source=clip.source_path,
            start_s=clip.in_seconds,
            end_s=clip.out_seconds,
            output_path=save_path,
            preset_name=clip.export_preset,
        )
        self._export_worker.progress.connect(self._progress.setValue)
        self._export_worker.finished.connect(self._on_export_done)
        self._export_worker.error.connect(self._on_export_error)
        self._export_worker.start()
        self.export_started.emit()

    def _on_export_done(self, path: str):
        self._progress.setValue(100)
        self._status_lbl.setText(f"✓ Guardado:\n{os.path.basename(path)}")
        self._btn_export.setEnabled(True)
        self.export_finished.emit(path)

    def _on_export_error(self, msg: str):
        self._status_lbl.setText(f"⚠ Error:\n{msg}")
        self._btn_export.setEnabled(True)
        self._progress.setVisible(False)
        self.export_error.emit(msg)
