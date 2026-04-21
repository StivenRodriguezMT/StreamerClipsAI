"""
ui/waveform_widget.py
Paints a mini waveform / timeline overview with in/out markers.
"""
import numpy as np
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QBrush


class WaveformWidget(QWidget):
    """
    Draws a simple amplitude waveform extracted from video frames' brightness
    (or flat bars if no audio data is provided). Supports scrubbing.
    """

    seek_requested = pyqtSignal(int)   # frame index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("waveform_widget")
        self.setMinimumHeight(54)
        self.setMaximumHeight(54)
        self.setCursor(Qt.PointingHandCursor)

        self._total_frames = 0
        self._current_frame = 0
        self._in_frame = -1
        self._out_frame = -1
        self._waveform_data = None   # np.ndarray, shape (N,), values 0–1

    # ------------------------------------------------------------------
    # Public setters
    # ------------------------------------------------------------------

    def set_total_frames(self, n: int):
        self._total_frames = n
        self._waveform_data = None
        self.update()

    def set_current_frame(self, f: int):
        self._current_frame = f
        self.update()

    def set_in_frame(self, f: int):
        self._in_frame = f
        self.update()

    def set_out_frame(self, f: int):
        self._out_frame = f
        self.update()

    def set_waveform_data(self, data: np.ndarray):
        """Pass normalised amplitude array (values 0–1)."""
        self._waveform_data = data
        self.update()

    def clear(self):
        self._total_frames = 0
        self._current_frame = 0
        self._in_frame = -1
        self._out_frame = -1
        self._waveform_data = None
        self.update()

    # ------------------------------------------------------------------
    # Mouse interaction (scrubbing)
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        self._seek(event.x())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._seek(event.x())

    def _seek(self, x: int):
        if self._total_frames <= 0:
            return
        ratio = max(0.0, min(1.0, x / self.width()))
        frame = int(ratio * self._total_frames)
        self.seek_requested.emit(frame)

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        w = self.width()
        h = self.height()

        # Background
        p.fillRect(0, 0, w, h, QColor("#07070f"))

        if self._total_frames <= 0:
            p.setPen(QColor("#1e1e35"))
            p.drawText(0, 0, w, h, Qt.AlignCenter, "Carga un video para ver la línea de tiempo")
            return

        # ---- Clip region highlight ----
        if self._in_frame >= 0 and self._out_frame > self._in_frame:
            x1 = int(self._in_frame / self._total_frames * w)
            x2 = int(self._out_frame / self._total_frames * w)
            clip_rect = QRect(x1, 0, x2 - x1, h)
            p.fillRect(clip_rect, QColor(124, 77, 255, 35))

        # ---- Waveform bars ----
        bar_count = min(w, 300)
        bar_w = max(1, w // bar_count)

        for i in range(bar_count):
            ratio = i / bar_count
            frame_pos = int(ratio * self._total_frames)

            # amplitude
            if self._waveform_data is not None and len(self._waveform_data) > 0:
                idx = int(ratio * len(self._waveform_data))
                idx = min(idx, len(self._waveform_data) - 1)
                amp = float(self._waveform_data[idx])
            else:
                # Pseudo-random static bars when no data
                amp = 0.15 + 0.25 * abs(np.sin(i * 0.37 + 1.2))

            bar_h = max(2, int(amp * (h - 8)))
            x = int(i / bar_count * w)
            y = (h - bar_h) // 2

            # Color: teal for selected region, purple elsewhere
            if self._in_frame >= 0 and self._out_frame > self._in_frame:
                if self._in_frame <= frame_pos <= self._out_frame:
                    color = QColor(0, 200, 180, 180)
                else:
                    color = QColor(40, 40, 80, 180)
            else:
                color = QColor(60, 60, 110, 180)

            p.fillRect(x, y, bar_w - 1, bar_h, color)

        # ---- In/Out markers ----
        if self._in_frame >= 0:
            x = int(self._in_frame / self._total_frames * w)
            pen = QPen(QColor("#00c853"), 2)
            p.setPen(pen)
            p.drawLine(x, 0, x, h)

        if self._out_frame >= 0 and self._out_frame > self._in_frame:
            x = int(self._out_frame / self._total_frames * w)
            pen = QPen(QColor("#ff5252"), 2)
            p.setPen(pen)
            p.drawLine(x, 0, x, h)

        # ---- Playhead ----
        if self._total_frames > 0:
            px = int(self._current_frame / self._total_frames * w)
            p.setPen(QPen(QColor("#ffffff"), 1))
            p.drawLine(px, 0, px, h)
            # Triangle head
            p.setBrush(QBrush(QColor("#ffffff")))
            p.setPen(Qt.NoPen)
            from PyQt5.QtCore import QPoint
            p.drawPolygon(QPoint(px - 4, 0), QPoint(px + 4, 0), QPoint(px, 7))

        p.end()
