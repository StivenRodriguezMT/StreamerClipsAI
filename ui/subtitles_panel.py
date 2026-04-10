"""
ui/subtitles_panel.py
Checkbox simple para activar subtítulos automáticos al exportar.
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox, QComboBox
from PyQt5.QtCore import Qt
from core.subtitles import WHISPER_MODELS


class SubtitlesOptions(QWidget):
    """
    Fila compacta con checkbox + selector de modelo.
    Se incrusta en la barra del timeline.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._chk = QCheckBox("🗣 Subtítulos automáticos")
        self._chk.setStyleSheet("color: #888888; font-size: 12px;")
        self._chk.setToolTip(
            "Al exportar, Whisper transcribirá el audio y\n"
            "quemará los subtítulos en el video automáticamente.\n"
            "Requiere: pip install openai-whisper torch"
        )
        layout.addWidget(self._chk)

        self._combo = QComboBox()
        self._combo.setFixedWidth(200)
        self._combo.setVisible(False)
        for name in WHISPER_MODELS.keys():
            self._combo.addItem(name)
        self._combo.setCurrentIndex(1)  # small por defecto
        layout.addWidget(self._combo)

        self._chk_gpu = QCheckBox("GPU")
        self._chk_gpu.setStyleSheet("color: #666666; font-size: 11px;")
        self._chk_gpu.setVisible(False)
        self._chk_gpu.setToolTip("Usar GPU Nvidia (más rápido)")
        layout.addWidget(self._chk_gpu)

        self._chk.toggled.connect(self._combo.setVisible)
        self._chk.toggled.connect(self._chk_gpu.setVisible)

    @property
    def enabled(self) -> bool:
        return self._chk.isChecked()

    @property
    def model_name(self) -> str:
        return WHISPER_MODELS[self._combo.currentText()]

    @property
    def use_gpu(self) -> bool:
        return self._chk_gpu.isChecked()
