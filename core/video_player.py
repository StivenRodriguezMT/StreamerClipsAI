"""
core/video_player.py
VLC renderiza video + audio directamente en el widget de la UI.
OpenCV solo se usa para obtener metadatos (fps, total de fotogramas).

Requiere: pip install python-vlc
          VLC 64-bit instalado en el sistema
"""
import cv2
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

try:
    import vlc
    VLC_AVAILABLE = True
except Exception:
    VLC_AVAILABLE = False


class VideoPlayer(QObject):
    """
    VLC maneja video + audio completo renderizando en un widget de Qt.
    Un QTimer emite la posición actual periódicamente para actualizar
    el slider y el timecode sin ningún hilo extra.
    """

    position_changed  = pyqtSignal(int)    # fotograma actual
    playback_finished = pyqtSignal()
    error_occurred    = pyqtSignal(str)
    vlc_missing       = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._fps          = 30.0
        self._total_frames = 0
        self._filepath     = ""
        self._vlc_ok       = False
        self._vlc_instance = None
        self._vlc_player   = None
        self._render_widget = None

        # Timer que emite la posición actual ~30 veces por segundo
        self._pos_timer = QTimer(self)
        self._pos_timer.setInterval(33)
        self._pos_timer.timeout.connect(self._emit_position)

        self._init_vlc()

    # ------------------------------------------------------------------
    # Inicialización
    # ------------------------------------------------------------------

    def _init_vlc(self):
        if not VLC_AVAILABLE:
            self.vlc_missing.emit()
            return
        try:
            self._vlc_instance = vlc.Instance()
            self._vlc_player   = self._vlc_instance.media_player_new()
            em = self._vlc_player.event_manager()
            em.event_attach(vlc.EventType.MediaPlayerEndReached,
                            self._on_vlc_end)
            self._vlc_ok = True
        except Exception as e:
            self._vlc_ok = False
            self.error_occurred.emit(f"Error iniciando VLC: {e}")

    def set_render_widget(self, widget):
        """Asignar el QWidget donde VLC dibujará el video."""
        self._render_widget = widget
        if self._vlc_ok:
            import sys
            hwnd = int(widget.winId())
            if sys.platform == "win32":
                self._vlc_player.set_hwnd(hwnd)
            elif sys.platform == "darwin":
                self._vlc_player.set_nsobject(hwnd)
            else:
                self._vlc_player.set_xwindow(hwnd)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def load(self, filepath: str) -> bool:
        """Abre un archivo de video. Devuelve True si tiene éxito."""
        # Obtener metadatos con OpenCV (rápido, no reproduce nada)
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            self.error_occurred.emit(f"No se puede abrir: {filepath}")
            return False

        self._fps          = cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        self._filepath = filepath

        if not self._vlc_ok:
            self.error_occurred.emit("VLC no disponible.")
            return False

        media = self._vlc_instance.media_new(filepath)
        self._vlc_player.set_media(media)
        return True

    def play(self):
        if self._vlc_ok:
            self._vlc_player.play()
            self._pos_timer.start()

    def pause(self):
        if self._vlc_ok:
            self._vlc_player.set_pause(1)
            self._pos_timer.stop()

    def seek(self, frame_index: int):
        if self._vlc_ok and self._fps:
            ms = int(frame_index / self._fps * 1000)
            self._vlc_player.set_time(ms)
            self.position_changed.emit(frame_index)

    def set_volume(self, volume: int):
        if self._vlc_ok:
            self._vlc_player.audio_set_volume(volume)

    def stop(self):
        self._pos_timer.stop()
        if self._vlc_ok:
            self._vlc_player.stop()

    def cleanup(self):
        self.stop()

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

    @property
    def total_frames(self) -> int:
        return self._total_frames

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def duration_seconds(self) -> float:
        return self._total_frames / self._fps if self._fps else 0.0

    @property
    def current_frame_index(self) -> int:
        if self._vlc_ok:
            ms = self._vlc_player.get_time()
            if ms >= 0:
                return int(ms / 1000.0 * self._fps)
        return 0

    @property
    def vlc_available(self) -> bool:
        return self._vlc_ok

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _emit_position(self):
        self.position_changed.emit(self.current_frame_index)

    def _on_vlc_end(self, event):
        self._pos_timer.stop()
        self.playback_finished.emit()
