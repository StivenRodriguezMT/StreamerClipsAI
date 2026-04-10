"""
ui/main_window.py
StreamerClipsAI — Interfaz estilo CapCut
  - Topbar con título y botón Exportar
  - Panel izquierdo: medios cargados
  - Centro: video grande
  - Panel derecho: lista de clips
  - Timeline inferior: slider + botones IN/OUT + crear clip
"""
import os
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QHBoxLayout, QWidget, QSlider,
    QSizePolicy, QStatusBar, QMessageBox, QFrame,
    QComboBox, QLineEdit, QProgressBar, QListWidget,
    QListWidgetItem, QSpacerItem
)
from PyQt5.QtGui import QKeySequence, QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSlot, QSize

from core.video_player import VideoPlayer
from core.clip_model import Clip
from core.ffmpeg_handler import EXPORT_PRESETS, ExportWorker, find_ffmpeg, seconds_to_hms
from core.subtitles import ExportWithSubtitlesWorker
from ui.waveform_widget import WaveformWidget
from ui.subtitles_panel import SubtitlesOptions
from ui.highlights_panel import HighlightsPanel
from core.highlight_detector import HighlightDetector
from ui.theme import DARK_THEME


def secs_to_tc(secs: float) -> str:
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("StreamerClipsAI")
        self.resize(1380, 820)
        self.setMinimumSize(1000, 650)
        self.setStyleSheet(DARK_THEME)

        # Estado
        self._source_path    = ""
        self._is_playing     = False
        self._slider_dragging = False
        self._in_frame       = -1
        self._out_frame      = -1
        self._fps            = 30.0
        self._total_frames   = 0
        self._current_frame  = 0
        self._ffmpeg_path    = None
        self._export_worker  = None
        self._clips          = []

        # Player
        self._player = VideoPlayer(self)
        self._player.position_changed.connect(self._on_position_changed)
        self._player.playback_finished.connect(self._on_playback_finished)
        self._player.error_occurred.connect(self._on_player_error)
        self._player.vlc_missing.connect(self._on_vlc_missing)

        self._build_ui()
        self._setup_shortcuts()

        self._status = QStatusBar()
        self._status.showMessage("Listo · Carga un video para comenzar")
        self.setStatusBar(self._status)

        self._player.set_render_widget(self._video_widget)

        # Intentar encontrar FFmpeg al inicio
        try:
            self._ffmpeg_path = find_ffmpeg()
        except RuntimeError:
            pass

    # ══════════════════════════════════════════════════════════════════
    # CONSTRUCCIÓN DE LA UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # 1) Topbar
        main.addWidget(self._build_topbar())

        # 2) Fila central (izquierda + video + derecha)
        center_row = QWidget()
        center_layout = QHBoxLayout(center_row)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        center_layout.addWidget(self._build_left_panel())
        center_layout.addWidget(self._build_center_panel(), stretch=1)
        center_layout.addWidget(self._build_right_panel())

        main.addWidget(center_row, stretch=1)

        # 3) Timeline inferior
        main.addWidget(self._build_timeline())

    # ── Topbar ────────────────────────────────────────────────────────

    def _build_topbar(self):
        bar = QWidget()
        bar.setObjectName("topbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # Logo
        title = QLabel("StreamerClips")
        title.setObjectName("app_title")
        sub = QLabel("AI")
        sub.setObjectName("app_subtitle")
        layout.addWidget(title)
        layout.addWidget(sub)

        layout.addStretch()

        # Botón exportar topbar
        self._btn_export_top = QPushButton("⬆  Exportar Clip")
        self._btn_export_top.setObjectName("btn_export_main")
        self._btn_export_top.setEnabled(False)
        self._btn_export_top.clicked.connect(self._export_clip)
        layout.addWidget(self._btn_export_top)

        return bar

    # ── Panel izquierdo ───────────────────────────────────────────────

    def _build_left_panel(self):
        panel = QWidget()
        panel.setObjectName("left_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("MEDIOS")
        title.setObjectName("left_panel_title")
        layout.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)

        # Botón cargar
        btn_load = QPushButton("＋  Agregar Video")
        btn_load.setObjectName("btn_load")
        btn_load.clicked.connect(self._load_video)
        btn_load.setToolTip("Agregar video a la lista (Ctrl+O)")
        layout.addWidget(btn_load)

        # Lista de videos cargados
        self._media_list = QListWidget()
        self._media_list.setSpacing(2)
        self._media_list.setToolTip("Doble clic para abrir el video")
        self._media_list.itemDoubleClicked.connect(self._on_media_double_clicked)
        self._media_list.currentRowChanged.connect(self._on_media_selected)
        layout.addWidget(self._media_list, stretch=1)

        # Botón quitar video
        self._btn_remove_media = QPushButton("✕  Quitar Video")
        self._btn_remove_media.setObjectName("btn_delete_clip")
        self._btn_remove_media.setEnabled(False)
        self._btn_remove_media.clicked.connect(self._remove_media)
        layout.addWidget(self._btn_remove_media)

        # Lista interna de rutas
        self._media_files = []   # lista de rutas absolutas

        return panel

    # ── Panel central (video + controles) ─────────────────────────────

    def _build_center_panel(self):
        panel = QWidget()
        panel.setObjectName("center_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Área de video
        video_container = QWidget()
        video_container.setObjectName("video_container")
        vc_layout = QVBoxLayout(video_container)
        vc_layout.setContentsMargins(0, 0, 0, 0)

        self._video_widget = QWidget()
        self._video_widget.setObjectName("video_widget")
        self._video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._video_widget.setAttribute(Qt.WA_OpaquePaintEvent)
        self._video_widget.setStyleSheet("background-color: #000000;")

        self._overlay_label = QLabel(
            "Arrastra un video aquí  o  haz clic en  ＋ Cargar Video",
            self._video_widget
        )
        self._overlay_label.setObjectName("overlay_text")
        self._overlay_label.setAlignment(Qt.AlignCenter)
        self._overlay_label.setStyleSheet(
            "color:#333333; font-size:14px; font-weight:500; background:transparent;"
        )

        vc_layout.addWidget(self._video_widget)
        layout.addWidget(video_container, stretch=1)

        # Controles de reproducción
        layout.addWidget(self._build_playback_controls())

        return panel

    def _build_playback_controls(self):
        bar = QWidget()
        bar.setObjectName("playback_controls")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        self._btn_back = QPushButton("⏮")
        self._btn_back.setObjectName("btn_skip")
        self._btn_back.setToolTip("Retroceder 10 s (←)")
        self._btn_back.clicked.connect(lambda: self._skip(-10))
        layout.addWidget(self._btn_back)

        self._btn_play = QPushButton("▶")
        self._btn_play.setObjectName("btn_play")
        self._btn_play.setToolTip("Reproducir / Pausar (Espacio)")
        self._btn_play.clicked.connect(self._toggle_play)
        layout.addWidget(self._btn_play)

        self._btn_fwd = QPushButton("⏭")
        self._btn_fwd.setObjectName("btn_skip")
        self._btn_fwd.setToolTip("Avanzar 10 s (→)")
        self._btn_fwd.clicked.connect(lambda: self._skip(10))
        layout.addWidget(self._btn_fwd)

        self._timecode_lbl = QLabel("00:00:00 / 00:00:00")
        self._timecode_lbl.setObjectName("timecode_main")
        layout.addWidget(self._timecode_lbl)

        layout.addStretch()

        layout.addWidget(QLabel("🔊"))
        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setObjectName("volume_slider")
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setFixedWidth(80)
        self._vol_slider.setToolTip("Volumen")
        self._vol_slider.valueChanged.connect(lambda v: self._player.set_volume(v))
        layout.addWidget(self._vol_slider)

        return bar

    # ── Panel derecho (lista de clips) ────────────────────────────────

    def _build_right_panel(self):
        panel = QWidget()
        panel.setObjectName("right_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("MIS CLIPS")
        title.setObjectName("right_panel_title")
        layout.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)

        self._clips_list = QListWidget()
        self._clips_list.setSpacing(2)
        layout.addWidget(self._clips_list, stretch=1)

        self._btn_delete = QPushButton("🗑  Eliminar clip")
        self._btn_delete.setObjectName("btn_delete_clip")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._delete_clip)
        layout.addWidget(self._btn_delete)

        # ── Panel de highlights ──
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #222222;")
        layout.addWidget(sep)

        self._highlights_panel = HighlightsPanel()
        self._highlights_panel.highlight_seek.connect(self._on_highlight_seek)
        self._highlights_panel.highlight_add.connect(self._on_highlight_add)
        layout.addWidget(self._highlights_panel, stretch=1)

        return panel

    # ── Timeline inferior ─────────────────────────────────────────────

    def _build_timeline(self):
        panel = QWidget()
        panel.setObjectName("timeline_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Barra de herramientas del timeline ──
        toolbar = QWidget()
        toolbar.setObjectName("timeline_toolbar")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(12, 0, 12, 0)
        tb_layout.setSpacing(8)

        # Botones IN / OUT
        self._btn_in = QPushButton("[ ENTRADA")
        self._btn_in.setObjectName("btn_set_in")
        self._btn_in.setToolTip("Marcar inicio del clip (I)")
        self._btn_in.clicked.connect(self._set_in)
        tb_layout.addWidget(self._btn_in)

        self._btn_out = QPushButton("SALIDA ]")
        self._btn_out.setObjectName("btn_set_out")
        self._btn_out.setToolTip("Marcar fin del clip (O)")
        self._btn_out.clicked.connect(self._set_out)
        tb_layout.addWidget(self._btn_out)

        # Display IN / OUT
        self._in_out_lbl = QLabel("IN: —   OUT: —   Dur: —")
        self._in_out_lbl.setObjectName("in_out_display")
        tb_layout.addWidget(self._in_out_lbl)

        tb_layout.addStretch()

        # Nombre del clip
        self._clip_name_edit = QLineEdit()
        self._clip_name_edit.setPlaceholderText("Nombre del clip (opcional)")
        self._clip_name_edit.setFixedWidth(180)
        tb_layout.addWidget(self._clip_name_edit)

        # Formato
        self._combo_format = QComboBox()
        self._combo_format.setFixedWidth(180)
        for k in EXPORT_PRESETS.keys():
            self._combo_format.addItem(k)
        tb_layout.addWidget(self._combo_format)

        # Botón crear clip
        self._btn_create = QPushButton("＋ Crear Clip")
        self._btn_create.setObjectName("btn_create_clip")
        self._btn_create.setEnabled(False)
        self._btn_create.clicked.connect(self._create_clip)
        tb_layout.addWidget(self._btn_create)

        layout.addWidget(toolbar)

        # ── Waveform / slider ──
        self._waveform = WaveformWidget()
        self._waveform.seek_requested.connect(self._on_waveform_seek)
        layout.addWidget(self._waveform, stretch=1)

        # ── Opciones de subtítulos ──
        self._subs_options = SubtitlesOptions()
        layout.addWidget(self._subs_options)

        # ── Slider del timeline ──
        slider_row = QWidget()
        slider_row.setStyleSheet("background:#0d0d0d;")
        slider_layout = QHBoxLayout(slider_row)
        slider_layout.setContentsMargins(12, 4, 12, 6)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setObjectName("timeline_slider")
        self._slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._slider.sliderMoved.connect(self._on_slider_moved)
        self._slider.sliderPressed.connect(lambda: setattr(self, '_slider_dragging', True))
        self._slider.sliderReleased.connect(self._on_slider_released)
        slider_layout.addWidget(self._slider)

        layout.addWidget(slider_row)

        # ── Barra de progreso de exportación ──
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        layout.addWidget(self._progress)

        return panel

    # ══════════════════════════════════════════════════════════════════
    # SHORTCUTS
    # ══════════════════════════════════════════════════════════════════

    def _setup_shortcuts(self):
        from PyQt5.QtWidgets import QShortcut
        QShortcut(QKeySequence("Space"),  self, self._toggle_play)
        QShortcut(QKeySequence("Ctrl+O"), self, self._load_video)
        QShortcut(QKeySequence("Left"),   self, lambda: self._skip(-10))
        QShortcut(QKeySequence("Right"),  self, lambda: self._skip(10))
        QShortcut(QKeySequence("I"),      self, self._set_in)
        QShortcut(QKeySequence("O"),      self, self._set_out)

    # ══════════════════════════════════════════════════════════════════
    # RESIZE — reposicionar overlay
    # ══════════════════════════════════════════════════════════════════

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_overlay_label'):
            w = self._video_widget.width()
            h = self._video_widget.height()
            self._overlay_label.setGeometry(0, (h - 40) // 2, w, 40)

    # ══════════════════════════════════════════════════════════════════
    # CARGA DE VIDEO
    # ══════════════════════════════════════════════════════════════════

    @pyqtSlot()
    def _load_video(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Agregar Videos",
            os.path.expanduser("~"),
            "Videos (*.mp4 *.avi *.mkv *.mov *.flv *.webm)"
        )
        if not files:
            return

        for file in files:
            if file not in self._media_files:
                self._media_files.append(file)
                name = os.path.basename(file)
                self._media_list.addItem(f"  {name}")

        self._btn_remove_media.setEnabled(True)

        # Si no hay video activo, abrir el primero
        if not self._source_path:
            self._media_list.setCurrentRow(0)
            self._open_media(self._media_files[0])

    def _on_media_double_clicked(self, item):
        row = self._media_list.row(item)
        if 0 <= row < len(self._media_files):
            self._open_media(self._media_files[row])

    def _on_media_selected(self, row):
        self._btn_remove_media.setEnabled(row >= 0)

    def _remove_media(self):
        row = self._media_list.currentRow()
        if row < 0:
            return
        file = self._media_files[row]
        self._media_list.takeItem(row)
        self._media_files.pop(row)

        # Si era el video activo, detener reproducción
        if file == self._source_path:
            self._player.stop()
            self._source_path = ""
            self._is_playing  = False
            self._btn_play.setText("▶")
            self._overlay_label.show()
            self._slider.setValue(0)
            self._waveform.set_total_frames(0)
            self._timecode_lbl.setText("00:00:00 / 00:00:00")
            self.setWindowTitle("StreamerClipsAI")
            self._btn_export_top.setEnabled(False)
            self._status.showMessage("Video eliminado de la lista")

        self._btn_remove_media.setEnabled(len(self._media_files) > 0)

    def _open_media(self, file: str):
        """Abre y reproduce un video de la lista."""
        self._player.stop()
        self._is_playing = False
        self._btn_play.setText("▶")
        self._in_frame  = -1
        self._out_frame = -1

        if not self._player.load(file):
            return

        self._source_path  = file
        self._fps          = self._player.fps
        self._total_frames = self._player.total_frames
        dur = self._player.duration_seconds

        self._slider.setMaximum(self._total_frames)
        self._slider.setValue(0)
        self._waveform.set_total_frames(self._total_frames)
        self._waveform.set_in_frame(-1)
        self._waveform.set_out_frame(-1)
        self._update_in_out_display()

        name = os.path.basename(file)
        self.setWindowTitle(f"StreamerClipsAI  ·  {name}")
        self._timecode_lbl.setText(f"00:00:00 / {secs_to_tc(dur)}")
        self._overlay_label.hide()

        self._status.showMessage(
            f"Cargado: {name}  |  {dur/60:.1f} min  |  {self._fps:.2f} fps  |  {self._total_frames:,} fotogramas"
        )

        self._player.play()
        self._player.set_volume(self._vol_slider.value())
        self._is_playing = True
        self._btn_play.setText("⏸")

    # ══════════════════════════════════════════════════════════════════
    # REPRODUCCIÓN
    # ══════════════════════════════════════════════════════════════════

    @pyqtSlot()
    def _toggle_play(self):
        if not self._source_path:
            self._load_video()
            return
        if self._is_playing:
            self._player.pause()
            self._is_playing = False
            self._btn_play.setText("▶")
        else:
            self._player.play()
            self._is_playing = True
            self._btn_play.setText("⏸")

    def _skip(self, seconds: float):
        if not self._source_path:
            return
        delta = int(seconds * (self._fps or 30))
        new_frame = max(0, min(self._current_frame + delta, self._total_frames - 1))
        self._player.seek(new_frame)
        self._slider.setValue(new_frame)

    # ══════════════════════════════════════════════════════════════════
    # SLIDER / WAVEFORM
    # ══════════════════════════════════════════════════════════════════

    def _on_slider_moved(self, pos: int):
        self._player.seek(pos)
        self._update_timecode(pos)

    def _on_slider_released(self):
        self._slider_dragging = False
        self._player.seek(self._slider.value())

    def _on_waveform_seek(self, frame: int):
        self._player.seek(frame)
        self._slider.setValue(frame)
        self._update_timecode(frame)

    def _update_timecode(self, frame: int):
        fps = self._fps or 30
        self._timecode_lbl.setText(
            f"{secs_to_tc(frame / fps)} / {secs_to_tc(self._player.duration_seconds)}"
        )

    # ══════════════════════════════════════════════════════════════════
    # IN / OUT / CLIPS
    # ══════════════════════════════════════════════════════════════════

    def _set_in(self):
        if not self._source_path:
            return
        self._in_frame = self._current_frame
        self._waveform.set_in_frame(self._in_frame)
        self._update_in_out_display()

    def _set_out(self):
        if not self._source_path:
            return
        self._out_frame = self._current_frame
        self._waveform.set_out_frame(self._out_frame)
        self._update_in_out_display()

    def _update_in_out_display(self):
        fps = self._fps or 30

        def fmt(f):
            return secs_to_tc(f / fps) if f >= 0 else "—"

        valid = self._in_frame >= 0 and self._out_frame > self._in_frame
        if valid:
            dur = (self._out_frame - self._in_frame) / fps
            m = int(dur // 60); s = dur % 60
            dur_str = f"{m}:{s:05.2f}"
        else:
            dur_str = "—"

        self._in_out_lbl.setText(
            f"IN: {fmt(self._in_frame)}   OUT: {fmt(self._out_frame)}   Dur: {dur_str}"
        )
        self._btn_create.setEnabled(valid)
        self._btn_export_top.setEnabled(valid and bool(self._source_path))

    def _create_clip(self):
        if not (self._in_frame >= 0 and self._out_frame > self._in_frame):
            return
        clip = Clip(
            source_path=self._source_path,
            in_frame=self._in_frame,
            out_frame=self._out_frame,
            fps=self._fps,
            label=self._clip_name_edit.text().strip(),
            export_preset=self._combo_format.currentText(),
        )
        self._clips.append(clip)

        dur = clip.duration_str
        preset_short = clip.export_preset.split("(")[0].strip()
        item = QListWidgetItem(f"  {clip.display_name()}\n  ⏱ {dur}  ·  {preset_short}")
        item.setData(Qt.UserRole, clip.id)
        self._clips_list.addItem(item)
        self._clips_list.setCurrentItem(item)
        self._btn_delete.setEnabled(True)
        self._clip_name_edit.clear()
        self._status.showMessage(f"✓ Clip '{clip.display_name()}' agregado")

    def _delete_clip(self):
        row = self._clips_list.currentRow()
        if row < 0:
            return
        item = self._clips_list.takeItem(row)
        clip_id = item.data(Qt.UserRole)
        self._clips = [c for c in self._clips if c.id != clip_id]
        self._btn_delete.setEnabled(self._clips_list.count() > 0)

    # ══════════════════════════════════════════════════════════════════
    # EXPORTAR
    # ══════════════════════════════════════════════════════════════════

    def _export_clip(self):
        if not self._ffmpeg_path:
            try:
                self._ffmpeg_path = find_ffmpeg()
            except RuntimeError as e:
                QMessageBox.warning(self, "FFmpeg no encontrado", str(e))
                return

        if not (self._in_frame >= 0 and self._out_frame > self._in_frame):
            return

        fps         = self._fps or 30
        in_s        = self._in_frame / fps
        out_s       = self._out_frame / fps
        preset_name = self._combo_format.currentText()
        preset      = EXPORT_PRESETS[preset_name]
        ext         = preset["ext"]

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Clip Como",
            f"clip.{ext}", f"Video (*.{ext})"
        )
        if not save_path:
            return

        self._btn_export_top.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)

        # ¿Exportar con subtítulos automáticos?
        if self._subs_options.enabled:
            self._status.showMessage("Exportando + transcribiendo + quemando subtítulos…")
            self._export_worker = ExportWithSubtitlesWorker(
                ffmpeg_path=self._ffmpeg_path,
                source=self._source_path,
                start_s=in_s,
                end_s=out_s,
                output_path=save_path,
                video_filter=preset["vf"],
                extra_args=preset["extra"],
                model_name=self._subs_options.model_name,
                use_gpu=self._subs_options.use_gpu,
            )
            self._export_worker.progress.connect(
                lambda pct, msg: (self._progress.setValue(pct), self._status.showMessage(msg))
            )
        else:
            self._status.showMessage("Exportando…")
            self._export_worker = ExportWorker(
                ffmpeg_path=self._ffmpeg_path,
                source=self._source_path,
                start_s=in_s,
                end_s=out_s,
                output_path=save_path,
                preset_name=preset_name,
            )
            self._export_worker.progress.connect(self._progress.setValue)

        self._export_worker.finished.connect(self._on_export_done)
        self._export_worker.error.connect(self._on_export_error)
        self._export_worker.start()

    def _on_export_done(self, path: str):
        self._progress.setValue(100)
        self._btn_export_top.setEnabled(True)
        self._status.showMessage(f"✓ Exportado: {os.path.basename(path)}", 8000)

    def _on_export_error(self, msg: str):
        self._progress.setVisible(False)
        self._btn_export_top.setEnabled(True)
        self._status.showMessage(f"⚠ Error: {msg}", 8000)
        QMessageBox.warning(self, "Error al exportar", msg)

    # ══════════════════════════════════════════════════════════════════
    # SEÑALES DEL PLAYER
    # ══════════════════════════════════════════════════════════════════

    @pyqtSlot(int)
    def _on_position_changed(self, frame: int):
        self._current_frame = frame
        if not self._slider_dragging:
            self._slider.setValue(frame)
        self._waveform.set_current_frame(frame)
        self._update_timecode(frame)

    @pyqtSlot()
    def _on_playback_finished(self):
        self._is_playing = False
        self._btn_play.setText("▶")
        self._status.showMessage("Reproducción finalizada")

    @pyqtSlot(str)
    def _on_player_error(self, msg: str):
        self._status.showMessage(f"⚠ {msg}")
        QMessageBox.warning(self, "Error de Video", msg)

    @pyqtSlot()
    def _on_vlc_missing(self):
        self._status.showMessage(
            "⚠ VLC no encontrado — instala VLC 64-bit desde https://www.videolan.org"
        )

    # ══════════════════════════════════════════════════════════════════
    # HIGHLIGHTS
    # ══════════════════════════════════════════════════════════════════

    @pyqtSlot(float)
    def _on_highlight_seek(self, seconds: float):
        """Ir al segundo del highlight en el video."""
        fps = self._fps or 30
        frame = int(seconds * fps)
        self._player.seek(frame)
        self._slider.setValue(frame)

    @pyqtSlot(object)
    def _on_highlight_add(self, highlight):
        """Agregar highlight como clip a la lista."""
        from core.clip_model import Clip
        fps = self._fps or 30
        clip = Clip(
            source_path  = self._source_path,
            in_frame     = int(highlight.start_sec * fps),
            out_frame    = int(highlight.end_sec   * fps),
            fps          = fps,
            label        = highlight.label(),
            export_preset= self._combo_format.currentText(),
        )
        self._clips.append(clip)
        item = QListWidgetItem(f"  {clip.display_name()}\n  ⏱ {clip.duration_str}")
        item.setData(Qt.UserRole, clip.id)
        self._clips_list.addItem(item)
        self._clips_list.setCurrentItem(item)
        self._btn_delete.setEnabled(True)
        self._status.showMessage(f"✓ Highlight agregado: {clip.display_name()}")

    # ══════════════════════════════════════════════════════════════════
    # CIERRE
    # ══════════════════════════════════════════════════════════════════

    def closeEvent(self, event):
        self._player.cleanup()
        event.accept()
