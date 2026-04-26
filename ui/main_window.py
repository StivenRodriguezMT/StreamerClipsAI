"""
ui/main_window.py
StreamerClipsAI — Interfaz estilo CapCut completa
"""
import os
import json
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QHBoxLayout, QWidget, QSlider,
    QSizePolicy, QStatusBar, QMessageBox, QFrame,
    QComboBox, QLineEdit, QProgressBar, QListWidget,
    QListWidgetItem, QScrollArea, QInputDialog,
    QColorDialog, QApplication, QSystemTrayIcon, QMenu
)
from PyQt5.QtGui import QKeySequence, QIcon, QColor
from PyQt5.QtCore import Qt, pyqtSlot, QSettings

from core.video_player import VideoPlayer
from core.clip_model import Clip
from core.ffmpeg_handler import EXPORT_PRESETS, ExportWorker, find_ffmpeg, seconds_to_hms
from core.subtitles import ExportWithSubtitlesWorker
from ui.waveform_widget import WaveformWidget
from ui.subtitles_panel import SubtitlesOptions
from ui.highlights_panel import HighlightsPanel
from ui.history_panel import HistoryPanel
from ui.profile_widget import ProfileWidget
from core.highlight_detector import HighlightDetector
from ui.theme import DARK_THEME


def secs_to_tc(secs: float) -> str:
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


CAPCUT_EXTRA = """
#topbar_capcut {
    background: #0d0d0d;
    border-bottom: 1px solid #1e1e1e;
    min-height: 44px; max-height: 44px;
}
#toolbar_tabs {
    background: #111111;
    border-bottom: 1px solid #1a1a1a;
    min-height: 56px; max-height: 56px;
}
#tab_btn {
    background: transparent; color: #555555; border: none;
    border-radius: 0; padding: 4px 6px; font-size: 11px; font-weight: 600; min-width: 52px;
}
#tab_btn:hover { color: #aaaaaa; }
#tab_btn_active {
    background: transparent; color: #ffffff; border: none;
    border-bottom: 2px solid #7c4dff; border-radius: 0;
    padding: 4px 6px; font-size: 11px; font-weight: 700; min-width: 52px;
}
#media_panel {
    background: #111111; border-right: 1px solid #1a1a1a;
    min-width: 240px; max-width: 240px;
}
#preview_panel { background: #0a0a0a; }
#props_panel {
    background: #111111; border-left: 1px solid #1a1a1a;
    min-width: 260px; max-width: 260px;
}
#props_title {
    font-size: 11px; font-weight: 700; letter-spacing: 2px;
    color: #444444; padding: 12px 16px 8px 16px;
}
#timeline_area {
    background: #0d0d0d; border-top: 1px solid #1a1a1a;
    min-height: 200px; max-height: 240px;
}
#timeline_ruler {
    background: #0a0a0a; border-bottom: 1px solid #1a1a1a;
    min-height: 24px; max-height: 24px;
}
#timeline_tools {
    background: #0d0d0d; border-bottom: 1px solid #1a1a1a;
    min-height: 38px; max-height: 38px;
}
#track_label {
    background: #111111; border-right: 1px solid #1a1a1a;
    min-width: 80px; max-width: 80px;
    color: #444444; font-size: 11px; padding: 0 8px;
}
#track_area { background: #0d0d0d; }
#btn_back_home {
    background: transparent; color: #666666; border: none;
    font-size: 18px; padding: 4px 8px; border-radius: 4px;
}
#btn_back_home:hover { color: #ffffff; background: #1e1e1e; }
#btn_import {
    background: #1e1e1e; color: #cccccc; border: 1px solid #2a2a2a;
    border-radius: 6px; padding: 6px 14px; font-size: 12px; font-weight: 600;
}
#btn_import:hover { background: #252525; border-color: #7c4dff; color: #ffffff; }
#btn_export_capcut {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5c2dff,stop:1 #7c4dff);
    color: #ffffff; border: none; border-radius: 6px;
    padding: 7px 20px; font-size: 12px; font-weight: 700;
}
#btn_export_capcut:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7c4dff,stop:1 #9c6dff);
}
#btn_export_capcut:disabled { background: #2a2a2a; color: #444444; }
#btn_play_preview {
    background: #ffffff; color: #000000; border: none; border-radius: 18px;
    min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px;
    font-size: 13px; font-weight: 700;
}
#btn_play_preview:hover { background: #e0e0e0; }
#timecode_preview { font-family: 'Courier New'; font-size: 12px; color: #666666; }
#btn_set_in {
    background: transparent; color: #00c853; border: 1px solid #1a3a25;
    border-radius: 5px; padding: 3px 10px; font-size: 11px; font-weight: 700;
}
#btn_set_in:hover { background: #0d2a1a; border-color: #00c853; }
#btn_set_out {
    background: transparent; color: #ff5252; border: 1px solid #3a1a1a;
    border-radius: 5px; padding: 3px 10px; font-size: 11px; font-weight: 700;
}
#btn_set_out:hover { background: #2a0d0d; border-color: #ff5252; }
#in_out_display { font-family: 'Courier New'; font-size: 11px; color: #555555; }
#btn_create_clip {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5c2dff,stop:1 #7c4dff);
    color: #ffffff; border: none; border-radius: 5px;
    padding: 4px 14px; font-size: 11px; font-weight: 700;
}
#btn_create_clip:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7c4dff,stop:1 #9c6dff);
}
#btn_create_clip:disabled { background: #2a2a2a; color: #444444; }
"""


class MainWindow(QMainWindow):

    def __init__(self, auth_manager=None):
        super().__init__()
        self.setWindowTitle("StreamerClipsAI")
        self.resize(1380, 820)
        self.setMinimumSize(1000, 650)
        self.setStyleSheet(DARK_THEME + CAPCUT_EXTRA)
        self.auth = auth_manager

        self._source_path     = ""
        self._is_playing      = False
        self._slider_dragging = False
        self._in_frame        = -1
        self._out_frame       = -1
        self._fps             = 30.0
        self._total_frames    = 0
        self._current_frame   = 0
        self._ffmpeg_path     = None
        self._export_worker   = None
        self._clips           = []
        self._detector        = None
        self._back_callback   = None
        self._loop_clip       = False
        self._preview_out_frame = 0
        self._in_color        = "#00c853"
        self._out_color       = "#ff5252"

        # QSettings para persistencia
        self._settings = QSettings("StreamerClipsAI", "Editor")
        self._default_output_dir = self._settings.value("output_dir", os.path.expanduser("~"))

        # Tray icon para notificaciones
        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip("StreamerClipsAI")

        # Drag & drop
        self.setAcceptDrops(True)

        self._player = VideoPlayer(self)
        self._player.position_changed.connect(self._on_position_changed)
        self._player.playback_finished.connect(self._on_playback_finished)
        self._player.error_occurred.connect(self._on_player_error)
        self._player.vlc_missing.connect(self._on_vlc_missing)

        self._build_ui()
        self._setup_shortcuts()

        self._status = QStatusBar()
        self._status.showMessage("Listo · Importa un video para comenzar")
        self.setStatusBar(self._status)

        self._player.set_render_widget(self._video_widget)

        try:
            self._ffmpeg_path = find_ffmpeg()
        except RuntimeError:
            pass

        # Recordar último video abierto (#3)
        last_video = self._settings.value("last_video", "")
        if last_video and os.path.exists(last_video):
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(300, lambda: self._open_media(last_video))

    def set_back_callback(self, fn):
        self._back_callback = fn

    # ══════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self._build_topbar())
        main.addWidget(self._build_toolbar_tabs())

        center = QWidget()
        cl = QHBoxLayout(center)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        cl.addWidget(self._build_media_panel())
        cl.addWidget(self._build_preview_panel(), stretch=1)
        cl.addWidget(self._build_props_panel())
        main.addWidget(center, stretch=1)

        main.addWidget(self._build_timeline())

    # ── Topbar ────────────────────────────────────────────────────────

    def _build_topbar(self):
        bar = QWidget()
        bar.setObjectName("topbar_capcut")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 16, 0)
        layout.setSpacing(8)

        btn_back = QPushButton("←")
        btn_back.setObjectName("btn_back_home")
        btn_back.setToolTip("Volver al inicio")
        btn_back.setFixedSize(32, 32)
        btn_back.clicked.connect(self._go_back)
        layout.addWidget(btn_back)

        btn_about = QPushButton("ℹ")
        btn_about.setObjectName("btn_back_home")
        btn_about.setToolTip("Acerca de StreamerClipsAI")
        btn_about.setFixedSize(32, 32)
        btn_about.clicked.connect(self._show_about)
        layout.addWidget(btn_about)

        title = QLabel("StreamerClips")
        title.setObjectName("app_title")
        sub = QLabel("AI")
        sub.setObjectName("app_subtitle")
        layout.addWidget(title)
        layout.addWidget(sub)

        layout.addSpacing(16)

        self._project_name = QLabel("Nuevo proyecto")
        self._project_name.setStyleSheet("color:#555555; font-size:12px; font-weight:600;")
        layout.addWidget(self._project_name)

        layout.addStretch()

        self._profile_widget = ProfileWidget()
        self._profile_widget.logout_requested.connect(self._do_logout)
        layout.addWidget(self._profile_widget)

        layout.addSpacing(12)

        self._clips_counter = QLabel("0 clips")
        self._clips_counter.setStyleSheet(
            "color:#444444; font-size:11px; font-weight:600; "
            "background:#1a1a1a; border:1px solid #2a2a2a; "
            "border-radius:10px; padding:3px 10px;"
        )
        layout.addWidget(self._clips_counter)

        self._btn_export_top = QPushButton("⬆  Exportar")
        self._btn_export_top.setObjectName("btn_export_capcut")
        self._btn_export_top.setEnabled(False)
        self._btn_export_top.clicked.connect(self._export_clip)
        layout.addWidget(self._btn_export_top)

        return bar

    # ── Barra de pestañas ─────────────────────────────────────────────

    def _build_toolbar_tabs(self):
        bar = QWidget()
        bar.setObjectName("toolbar_tabs")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(2)

        tabs = [("📁", "Medios"), ("🎵", "Audio"), ("✏️", "Texto"),
                ("✨", "Efectos"), ("🔀", "Transiciones"), ("💬", "Subtítulos"), ("🤖", "IA")]

        for i, (icon, label) in enumerate(tabs):
            btn = QPushButton(f"{icon}\n{label}")
            btn.setObjectName("tab_btn_active" if i == 0 else "tab_btn")
            btn.setFixedSize(60, 50)
            layout.addWidget(btn)

        layout.addStretch()

        btn_import = QPushButton("＋  Importar")
        btn_import.setObjectName("btn_import")
        btn_import.clicked.connect(self._load_video)
        layout.addWidget(btn_import)

        return bar

    # ── Panel medios ──────────────────────────────────────────────────

    def _build_media_panel(self):
        panel = QWidget()
        panel.setObjectName("media_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sub_tabs = QWidget()
        sub_tabs.setStyleSheet("background:#0d0d0d; border-bottom:1px solid #1a1a1a;")
        st = QHBoxLayout(sub_tabs)
        st.setContentsMargins(8, 6, 8, 0)
        st.setSpacing(0)
        for i, lbl in enumerate(["Importar", "Grabar"]):
            btn = QPushButton(lbl)
            btn.setObjectName("tab_btn_active" if i == 0 else "tab_btn")
            btn.setFixedHeight(28)
            st.addWidget(btn)
        st.addStretch()
        layout.addWidget(sub_tabs)

        filter_row = QWidget()
        filter_row.setStyleSheet("background:#0d0d0d;")
        fl = QHBoxLayout(filter_row)
        fl.setContentsMargins(8, 4, 8, 4)
        lbl = QLabel("Todos")
        lbl.setStyleSheet("color:#888888; font-size:11px; font-weight:700;")
        fl.addWidget(lbl)
        fl.addStretch()
        layout.addWidget(filter_row)

        self._media_list = QListWidget()
        self._media_list.setSpacing(2)
        self._media_list.setToolTip("Doble clic para abrir el video")
        self._media_list.itemDoubleClicked.connect(self._on_media_double_clicked)
        self._media_list.setStyleSheet("""
            QListWidget { background:#111111; border:none; }
            QListWidget::item {
                background:#161616; border:1px solid #1e1e1e; border-radius:6px;
                padding:8px; margin:4px 8px; color:#aaaaaa;
            }
            QListWidget::item:selected { background:#1e1e2a; border-color:#7c4dff; color:#ffffff; }
            QListWidget::item:hover { background:#1a1a1a; }
        """)
        layout.addWidget(self._media_list, stretch=1)

        btn_remove = QPushButton("✕  Quitar")
        btn_remove.setObjectName("btn_delete_clip")
        btn_remove.clicked.connect(self._remove_media)
        layout.addWidget(btn_remove)

        self._media_files = []
        return panel

    # ── Panel preview ─────────────────────────────────────────────────

    def _build_preview_panel(self):
        panel = QWidget()
        panel.setObjectName("preview_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        ph = QWidget()
        ph.setStyleSheet("background:#0d0d0d; border-bottom:1px solid #1a1a1a;")
        ph_l = QHBoxLayout(ph)
        ph_l.setContentsMargins(12, 6, 12, 6)
        lbl = QLabel("Reproductor")
        lbl.setStyleSheet("color:#555555; font-size:11px; font-weight:700; letter-spacing:1px;")
        ph_l.addWidget(lbl)
        ph_l.addStretch()
        for ratio in ["Completa", "Relación"]:
            btn = QPushButton(ratio)
            btn.setStyleSheet("""
                QPushButton { background:#1a1a1a; color:#666666; border:1px solid #222222;
                    border-radius:4px; padding:3px 8px; font-size:10px; }
                QPushButton:hover { color:#ffffff; }
            """)
            ph_l.addWidget(btn)
        layout.addWidget(ph)

        # Video
        self._video_widget = QWidget()
        self._video_widget.setObjectName("video_widget")
        self._video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._video_widget.setAttribute(Qt.WA_OpaquePaintEvent)
        self._video_widget.setStyleSheet("background:#000000;")

        self._overlay_label = QLabel(
            "Arrastra un video aquí  o  haz clic en  ＋ Importar",
            self._video_widget
        )
        self._overlay_label.setAlignment(Qt.AlignCenter)
        self._overlay_label.setStyleSheet("color:#333333; font-size:13px; background:transparent;")

        layout.addWidget(self._video_widget, stretch=1)
        layout.addWidget(self._build_preview_controls())
        return panel

    def _build_preview_controls(self):
        bar = QWidget()
        bar.setStyleSheet("background:#0d0d0d; border-top:1px solid #1a1a1a;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(8)

        # Timecode clickeable para copiar al portapapeles (#11)
        self._timecode_lbl = QLabel("00:00:00.00")
        self._timecode_lbl.setObjectName("timecode_preview")
        self._timecode_lbl.setToolTip("Clic para copiar timecode al portapapeles")
        self._timecode_lbl.setCursor(Qt.PointingHandCursor)
        self._timecode_lbl.mousePressEvent = lambda e: self._copy_timecode()
        layout.addWidget(self._timecode_lbl)

        # FPS y resolución (#18)
        self._video_info_lbl = QLabel("")
        self._video_info_lbl.setStyleSheet("color:#333333; font-size:10px; font-family:'Courier New';")
        layout.addWidget(self._video_info_lbl)

        layout.addStretch()

        # Ir al inicio (#19)
        btn_start = QPushButton("⏮")
        btn_start.setObjectName("btn_skip")
        btn_start.setToolTip("Ir al inicio del video (Home)")
        btn_start.clicked.connect(lambda: self._goto_frame(0))
        layout.addWidget(btn_start)

        # Retroceder 10s
        btn_back = QPushButton("◀◀")
        btn_back.setObjectName("btn_skip")
        btn_back.setToolTip("Retroceder 10s (←)")
        btn_back.clicked.connect(lambda: self._skip(-10))
        layout.addWidget(btn_back)

        self._btn_play = QPushButton("▶")
        self._btn_play.setObjectName("btn_play_preview")
        self._btn_play.setToolTip("Reproducir/Pausar (Espacio)")
        self._btn_play.clicked.connect(self._toggle_play)
        layout.addWidget(self._btn_play)

        # Avanzar 10s
        btn_fwd = QPushButton("▶▶")
        btn_fwd.setObjectName("btn_skip")
        btn_fwd.setToolTip("Avanzar 10s (→)")
        btn_fwd.clicked.connect(lambda: self._skip(10))
        layout.addWidget(btn_fwd)

        # Ir al final (#19)
        btn_end = QPushButton("⏭")
        btn_end.setObjectName("btn_skip")
        btn_end.setToolTip("Ir al final del video (End)")
        btn_end.clicked.connect(lambda: self._goto_frame(self._total_frames - 1))
        layout.addWidget(btn_end)

        layout.addStretch()

        # Captura de pantalla (#6)
        btn_screenshot = QPushButton("📷")
        btn_screenshot.setObjectName("btn_skip")
        btn_screenshot.setToolTip("Capturar frame actual (S)")
        btn_screenshot.clicked.connect(self._screenshot)
        layout.addWidget(btn_screenshot)

        layout.addWidget(QLabel("🔊"))
        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setObjectName("volume_slider")
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setFixedWidth(70)
        self._vol_slider.valueChanged.connect(lambda v: self._player.set_volume(v))
        # Volumen con rueda del mouse (#17)
        self._vol_slider.wheelEvent = self._vol_wheel
        layout.addWidget(self._vol_slider)

        self._timecode_total = QLabel("/ 00:00:00.00")
        self._timecode_total.setObjectName("timecode_preview")
        layout.addWidget(self._timecode_total)

        return bar

    # ── Panel propiedades ─────────────────────────────────────────────

    def _build_props_panel(self):
        from PyQt5.QtWidgets import QStackedWidget, QDoubleSpinBox, QSpinBox, QCheckBox
        panel = QWidget()
        panel.setObjectName("props_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Tabs clickeables ──
        tab_row = QWidget()
        tab_row.setStyleSheet("background:#0d0d0d; border-bottom:1px solid #1a1a1a;")
        tr = QHBoxLayout(tab_row)
        tr.setContentsMargins(8, 0, 8, 0)
        tr.setSpacing(0)
        self._prop_tab_btns = []
        for i, t in enumerate(["Video", "Audio", "Velocidad", "Ajustar"]):
            btn = QPushButton(t)
            btn.setObjectName("tab_btn_active" if i == 0 else "tab_btn")
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda _, idx=i: self._switch_props_tab(idx))
            tr.addWidget(btn)
            self._prop_tab_btns.append(btn)
        tr.addStretch()
        layout.addWidget(tab_row)

        # ── Stack de contenido ──
        self._props_stack = QStackedWidget()
        self._props_stack.setStyleSheet("background:#111111;")

        # ─ Tab 0: VIDEO ─
        self._props_stack.addWidget(self._build_video_tab())
        # ─ Tab 1: AUDIO ─
        self._props_stack.addWidget(self._build_audio_tab())
        # ─ Tab 2: VELOCIDAD ─
        self._props_stack.addWidget(self._build_speed_tab())
        # ─ Tab 3: AJUSTAR ─
        self._props_stack.addWidget(self._build_adjust_tab())

        layout.addWidget(self._props_stack, stretch=1)

        self._history_panel = HistoryPanel(self.auth) if self.auth else None
        if self._history_panel:
            sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
            sep2.setStyleSheet("color:#1a1a1a;")
            layout.addWidget(sep2)
            layout.addWidget(self._history_panel)

        return panel

    def _switch_props_tab(self, idx: int):
        self._props_stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._prop_tab_btns):
            btn.setObjectName("tab_btn_active" if i == idx else "tab_btn")
            btn.setStyle(btn.style())

    # ─── Tab Video ────────────────────────────────────────────────────
    def _build_video_tab(self):
        from PyQt5.QtWidgets import QStackedWidget, QDoubleSpinBox, QSpinBox
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        def _lbl(txt):
            l = QLabel(txt)
            l.setStyleSheet("color:#666666; font-size:11px; font-weight:600; letter-spacing:1px;")
            return l

        def _sep():
            f = QFrame(); f.setFrameShape(QFrame.HLine)
            f.setStyleSheet("color:#1e1e1e;"); return f

        # MIS CLIPS (movido aquí)
        layout.addWidget(_lbl("MIS CLIPS"))
        self._clips_list = QListWidget()
        self._clips_list.setSpacing(2)
        self._clips_list.setMaximumHeight(130)
        self._clips_list.setStyleSheet("""
            QListWidget { background:transparent; border:none; }
            QListWidget::item {
                background:#161616; border:1px solid #1e1e1e; border-radius:5px;
                padding:6px 10px; margin:2px 0px; color:#aaaaaa; font-size:11px;
            }
            QListWidget::item:selected { background:#1e1e2a; border-color:#7c4dff; color:#fff; }
        """)
        self._clips_list.itemDoubleClicked.connect(self._rename_clip)
        layout.addWidget(self._clips_list)

        self._total_dur_lbl = QLabel("Duración total: —")
        self._total_dur_lbl.setStyleSheet("color:#444444; font-size:10px;")
        layout.addWidget(self._total_dur_lbl)

        clip_btns = QHBoxLayout()
        clip_btns.setSpacing(4)
        self._btn_delete = QPushButton("🗑")
        self._btn_delete.setObjectName("btn_delete_clip")
        self._btn_delete.setFixedSize(28, 28)
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._delete_clip)
        clip_btns.addWidget(self._btn_delete)
        for icon, tip, fn in [
            ("⧉", "Duplicar", self._duplicate_clip),
            ("A↓", "Ordenar nombre", lambda: self._sort_clips("name")),
            ("⏱", "Ordenar duración", lambda: self._sort_clips("duration")),
        ]:
            b = QPushButton(icon)
            b.setObjectName("btn_delete_clip")
            b.setToolTip(tip)
            b.setFixedSize(28, 28)
            b.clicked.connect(fn)
            clip_btns.addWidget(b)
        clip_btns.addStretch()
        layout.addLayout(clip_btns)

        layout.addWidget(_sep())

        # TRANSFORMACIÓN
        layout.addWidget(_lbl("TRANSFORMACIÓN"))

        # Escala
        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Escala"))
        self._scale_slider = QSlider(Qt.Horizontal)
        self._scale_slider.setRange(10, 300)
        self._scale_slider.setValue(100)
        self._scale_slider.valueChanged.connect(self._on_transform_changed)
        scale_row.addWidget(self._scale_slider, stretch=1)
        self._scale_val = QLabel("100%")
        self._scale_val.setStyleSheet("color:#aaa; font-size:11px; min-width:36px;")
        self._scale_slider.valueChanged.connect(lambda v: self._scale_val.setText(f"{v}%"))
        scale_row.addWidget(self._scale_val)
        layout.addLayout(scale_row)

        # Posición X Y
        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("X"))
        self._pos_x = QSlider(Qt.Horizontal)
        self._pos_x.setRange(-500, 500)
        self._pos_x.setValue(0)
        self._pos_x.valueChanged.connect(self._on_transform_changed)
        pos_row.addWidget(self._pos_x, stretch=1)
        self._pos_x_val = QLabel("0")
        self._pos_x_val.setStyleSheet("color:#aaa; font-size:11px; min-width:30px;")
        self._pos_x.valueChanged.connect(lambda v: self._pos_x_val.setText(str(v)))
        pos_row.addWidget(self._pos_x_val)
        layout.addLayout(pos_row)

        pos_row2 = QHBoxLayout()
        pos_row2.addWidget(QLabel("Y"))
        self._pos_y = QSlider(Qt.Horizontal)
        self._pos_y.setRange(-500, 500)
        self._pos_y.setValue(0)
        self._pos_y.valueChanged.connect(self._on_transform_changed)
        pos_row2.addWidget(self._pos_y, stretch=1)
        self._pos_y_val = QLabel("0")
        self._pos_y_val.setStyleSheet("color:#aaa; font-size:11px; min-width:30px;")
        self._pos_y.valueChanged.connect(lambda v: self._pos_y_val.setText(str(v)))
        pos_row2.addWidget(self._pos_y_val)
        layout.addLayout(pos_row2)

        # Rotación
        rot_row = QHBoxLayout()
        rot_row.addWidget(QLabel("Girar"))
        self._rotation_slider = QSlider(Qt.Horizontal)
        self._rotation_slider.setRange(-180, 180)
        self._rotation_slider.setValue(0)
        self._rotation_slider.valueChanged.connect(self._on_transform_changed)
        rot_row.addWidget(self._rotation_slider, stretch=1)
        self._rot_val = QLabel("0°")
        self._rot_val.setStyleSheet("color:#aaa; font-size:11px; min-width:36px;")
        self._rotation_slider.valueChanged.connect(lambda v: self._rot_val.setText(f"{v}°"))
        rot_row.addWidget(self._rot_val)
        layout.addLayout(rot_row)

        # Botón resetear transformación
        btn_reset_tx = QPushButton("↺  Resetear transformación")
        btn_reset_tx.setStyleSheet("""
            QPushButton { background:#1a1a1a; color:#666; border:1px solid #222;
                border-radius:5px; padding:5px; font-size:11px; }
            QPushButton:hover { color:#fff; }
        """)
        btn_reset_tx.clicked.connect(self._reset_transform)
        layout.addWidget(btn_reset_tx)

        layout.addWidget(_sep())

        # Highlights panel
        self._highlights_panel = HighlightsPanel()
        self._highlights_panel.highlight_seek.connect(self._on_highlight_seek)
        self._highlights_panel.highlight_add.connect(self._on_highlight_add)
        layout.addWidget(self._highlights_panel, stretch=1)

        layout.addStretch()
        return w

    # ─── Tab Audio ────────────────────────────────────────────────────
    def _build_audio_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(12)

        def _lbl(txt):
            l = QLabel(txt)
            l.setStyleSheet("color:#666666; font-size:11px; font-weight:600; letter-spacing:1px;")
            return l

        layout.addWidget(_lbl("BÁSICO"))

        # Volumen dB
        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("Volumen"))
        self._audio_vol_slider = QSlider(Qt.Horizontal)
        self._audio_vol_slider.setRange(-20, 20)
        self._audio_vol_slider.setValue(0)
        vol_row.addWidget(self._audio_vol_slider, stretch=1)
        self._audio_vol_lbl = QLabel("0.0 dB")
        self._audio_vol_lbl.setStyleSheet("color:#aaa; font-size:11px; min-width:44px;")
        self._audio_vol_slider.valueChanged.connect(
            lambda v: self._audio_vol_lbl.setText(f"{v:+.1f} dB")
        )
        vol_row.addWidget(self._audio_vol_lbl)
        layout.addLayout(vol_row)

        # Fade in
        fade_in_row = QHBoxLayout()
        fade_in_row.addWidget(QLabel("Fade in"))
        self._fade_in_slider = QSlider(Qt.Horizontal)
        self._fade_in_slider.setRange(0, 50)
        self._fade_in_slider.setValue(0)
        fade_in_row.addWidget(self._fade_in_slider, stretch=1)
        self._fade_in_lbl = QLabel("0.0s")
        self._fade_in_lbl.setStyleSheet("color:#aaa; font-size:11px; min-width:36px;")
        self._fade_in_slider.valueChanged.connect(
            lambda v: self._fade_in_lbl.setText(f"{v/10:.1f}s")
        )
        fade_in_row.addWidget(self._fade_in_lbl)
        layout.addLayout(fade_in_row)

        # Fade out
        fade_out_row = QHBoxLayout()
        fade_out_row.addWidget(QLabel("Fade out"))
        self._fade_out_slider = QSlider(Qt.Horizontal)
        self._fade_out_slider.setRange(0, 50)
        self._fade_out_slider.setValue(0)
        fade_out_row.addWidget(self._fade_out_slider, stretch=1)
        self._fade_out_lbl = QLabel("0.0s")
        self._fade_out_lbl.setStyleSheet("color:#aaa; font-size:11px; min-width:36px;")
        self._fade_out_slider.valueChanged.connect(
            lambda v: self._fade_out_lbl.setText(f"{v/10:.1f}s")
        )
        fade_out_row.addWidget(self._fade_out_lbl)
        layout.addLayout(fade_out_row)

        btn_reset_audio = QPushButton("↺  Resetear audio")
        btn_reset_audio.setStyleSheet("""
            QPushButton { background:#1a1a1a; color:#666; border:1px solid #222;
                border-radius:5px; padding:5px; font-size:11px; }
            QPushButton:hover { color:#fff; }
        """)
        btn_reset_audio.clicked.connect(self._reset_audio)
        layout.addWidget(btn_reset_audio)
        layout.addStretch()
        return w

    # ─── Tab Velocidad ────────────────────────────────────────────────
    def _build_speed_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(12)

        def _lbl(txt):
            l = QLabel(txt)
            l.setStyleSheet("color:#666666; font-size:11px; font-weight:600; letter-spacing:1px;")
            return l

        layout.addWidget(_lbl("VELOCIDAD"))

        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Velocidad"))
        self._speed_slider = QSlider(Qt.Horizontal)
        self._speed_slider.setRange(1, 40)   # 0.1x - 4.0x
        self._speed_slider.setValue(10)       # 1.0x
        speed_row.addWidget(self._speed_slider, stretch=1)
        self._speed_lbl = QLabel("1.00x")
        self._speed_lbl.setStyleSheet("color:#7c4dff; font-size:12px; font-weight:700; min-width:40px;")
        self._speed_slider.valueChanged.connect(
            lambda v: self._speed_lbl.setText(f"{v/10:.2f}x")
        )
        speed_row.addWidget(self._speed_lbl)
        layout.addLayout(speed_row)

        # Marcadores de velocidad
        marks_row = QHBoxLayout()
        for label, val in [("0.1x", 1), ("0.5x", 5), ("1x", 10), ("2x", 20), ("4x", 40)]:
            b = QPushButton(label)
            b.setFixedHeight(24)
            b.setStyleSheet("""
                QPushButton { background:#1a1a1a; color:#666; border:1px solid #222;
                    border-radius:4px; font-size:10px; }
                QPushButton:hover { color:#fff; border-color:#7c4dff; }
            """)
            b.clicked.connect(lambda _, v=val: self._speed_slider.setValue(v))
            marks_row.addWidget(b)
        layout.addLayout(marks_row)

        # Duración estimada
        self._speed_dur_lbl = QLabel("Duración estimada: —")
        self._speed_dur_lbl.setStyleSheet("color:#555555; font-size:11px;")
        self._speed_slider.valueChanged.connect(self._update_speed_duration)
        layout.addWidget(self._speed_dur_lbl)

        btn_reset_speed = QPushButton("↺  Resetear velocidad")
        btn_reset_speed.setStyleSheet("""
            QPushButton { background:#1a1a1a; color:#666; border:1px solid #222;
                border-radius:5px; padding:5px; font-size:11px; }
            QPushButton:hover { color:#fff; }
        """)
        btn_reset_speed.clicked.connect(lambda: self._speed_slider.setValue(10))
        layout.addWidget(btn_reset_speed)
        layout.addStretch()
        return w

    # ─── Tab Ajustar ─────────────────────────────────────────────────
    def _build_adjust_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        def _lbl(txt):
            l = QLabel(txt)
            l.setStyleSheet("color:#666666; font-size:11px; font-weight:600; letter-spacing:1px;")
            return l

        def _slider_row(label, attr, min_val, max_val, default):
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            s = QSlider(Qt.Horizontal)
            s.setRange(min_val, max_val)
            s.setValue(default)
            setattr(self, attr, s)
            row.addWidget(s, stretch=1)
            lbl = QLabel(str(default))
            lbl.setStyleSheet("color:#aaa; font-size:11px; min-width:30px;")
            s.valueChanged.connect(lambda v, l=lbl: l.setText(str(v)))
            row.addWidget(lbl)
            return row

        layout.addWidget(_lbl("COLOR Y LUZ"))
        layout.addLayout(_slider_row("Brillo",     "_adj_brightness", -100, 100, 0))
        layout.addLayout(_slider_row("Contraste",  "_adj_contrast",   -100, 100, 0))
        layout.addLayout(_slider_row("Saturación", "_adj_saturation", -100, 100, 0))
        layout.addLayout(_slider_row("Nitidez",    "_adj_sharpness",     0, 100, 0))

        def _sep():
            f = QFrame(); f.setFrameShape(QFrame.HLine)
            f.setStyleSheet("color:#1e1e1e;"); return f
        layout.addWidget(_sep())

        layout.addWidget(_lbl("TEMPERATURA"))
        layout.addLayout(_slider_row("Temperatura", "_adj_temp",  -100, 100, 0))
        layout.addLayout(_slider_row("Tono",        "_adj_tint",  -100, 100, 0))

        btn_reset_adj = QPushButton("↺  Resetear ajustes")
        btn_reset_adj.setStyleSheet("""
            QPushButton { background:#1a1a1a; color:#666; border:1px solid #222;
                border-radius:5px; padding:5px; font-size:11px; }
            QPushButton:hover { color:#fff; }
        """)
        btn_reset_adj.clicked.connect(self._reset_adjust)
        layout.addWidget(btn_reset_adj)
        layout.addStretch()
        return w

    # ── Timeline ──────────────────────────────────────────────────────

    def _build_timeline(self):
        panel = QWidget()
        panel.setObjectName("timeline_area")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Herramientas
        tools = QWidget()
        tools.setObjectName("timeline_tools")
        tl = QHBoxLayout(tools)
        tl.setContentsMargins(8, 0, 12, 0)
        tl.setSpacing(6)

        for icon, tip in [("↩", "Deshacer"), ("↪", "Rehacer"), ("|◄", "Dividir"),
                          ("✂", "Cortar"), ("🗑", "Eliminar")]:
            btn = QPushButton(icon)
            btn.setToolTip(tip)
            btn.setFixedSize(28, 28)
            btn.setStyleSheet("""
                QPushButton { background:#1a1a1a; color:#666; border:1px solid #222;
                    border-radius:4px; font-size:12px; }
                QPushButton:hover { color:#fff; border-color:#555; }
            """)
            tl.addWidget(btn)

        tl.addSpacing(12)

        self._btn_in = QPushButton("[ ENTRADA")
        self._btn_in.setObjectName("btn_set_in")
        self._btn_in.setToolTip("Marcar inicio del clip (I)")
        self._btn_in.clicked.connect(self._set_in)
        tl.addWidget(self._btn_in)

        self._btn_out = QPushButton("SALIDA ]")
        self._btn_out.setObjectName("btn_set_out")
        self._btn_out.setToolTip("Marcar fin del clip (O)")
        self._btn_out.clicked.connect(self._set_out)
        tl.addWidget(self._btn_out)

        # Resetear IN/OUT (#12)
        btn_reset = QPushButton("✕")
        btn_reset.setToolTip("Resetear IN/OUT (R)")
        btn_reset.setFixedSize(22, 22)
        btn_reset.setStyleSheet("QPushButton{background:#1a1a1a;color:#666;border:1px solid #222;border-radius:4px;font-size:10px;}QPushButton:hover{color:#ff5252;}")
        btn_reset.clicked.connect(self._reset_in_out)
        tl.addWidget(btn_reset)

        # Seleccionar todo el video (#16)
        btn_all = QPushButton("◼")
        btn_all.setToolTip("Seleccionar todo el video (A)")
        btn_all.setFixedSize(22, 22)
        btn_all.setStyleSheet("QPushButton{background:#1a1a1a;color:#666;border:1px solid #222;border-radius:4px;font-size:10px;}QPushButton:hover{color:#7c4dff;}")
        btn_all.clicked.connect(self._select_all_video)
        tl.addWidget(btn_all)

        # Loop (#8)
        self._btn_loop = QPushButton("🔁")
        self._btn_loop.setToolTip("Loop del clip (L)")
        self._btn_loop.setFixedSize(22, 22)
        self._btn_loop.setCheckable(True)
        self._btn_loop.setStyleSheet("QPushButton{background:#1a1a1a;color:#666;border:1px solid #222;border-radius:4px;font-size:10px;}QPushButton:checked{color:#7c4dff;border-color:#7c4dff;}QPushButton:hover{color:#aaa;}")
        self._btn_loop.toggled.connect(lambda c: setattr(self, '_loop_clip', c))
        tl.addWidget(self._btn_loop)

        self._in_out_lbl = QLabel("IN: —   OUT: —   Dur: —")
        self._in_out_lbl.setObjectName("in_out_display")
        tl.addWidget(self._in_out_lbl)

        # Tamaño estimado (#13)
        self._size_lbl = QLabel("")
        self._size_lbl.setStyleSheet("color:#444444; font-size:10px; font-family:'Courier New';")
        tl.addWidget(self._size_lbl)

        tl.addStretch()

        self._clip_name_edit = QLineEdit()
        self._clip_name_edit.setPlaceholderText("Nombre del clip")
        self._clip_name_edit.setFixedWidth(150)
        tl.addWidget(self._clip_name_edit)

        self._combo_format = QComboBox()
        self._combo_format.setFixedWidth(160)
        for k in EXPORT_PRESETS.keys():
            self._combo_format.addItem(k)
        self._combo_format.currentTextChanged.connect(self._on_format_changed)
        tl.addWidget(self._combo_format)

        # Carpeta de salida (#7)
        btn_outdir = QPushButton("📁")
        btn_outdir.setToolTip("Carpeta de salida por defecto")
        btn_outdir.setFixedSize(28, 28)
        btn_outdir.setStyleSheet("QPushButton{background:#1a1a1a;color:#666;border:1px solid #222;border-radius:4px;}QPushButton:hover{color:#fff;}")
        btn_outdir.clicked.connect(self._set_output_dir)
        tl.addWidget(btn_outdir)

        # Color IN (#20)
        self._btn_in_color = QPushButton()
        self._btn_in_color.setToolTip("Color marcador IN")
        self._btn_in_color.setFixedSize(16, 16)
        self._btn_in_color.setStyleSheet(f"background:{self._in_color}; border-radius:8px; border:none;")
        self._btn_in_color.clicked.connect(self._pick_in_color)
        tl.addWidget(self._btn_in_color)

        # Color OUT (#20)
        self._btn_out_color = QPushButton()
        self._btn_out_color.setToolTip("Color marcador OUT")
        self._btn_out_color.setFixedSize(16, 16)
        self._btn_out_color.setStyleSheet(f"background:{self._out_color}; border-radius:8px; border:none;")
        self._btn_out_color.clicked.connect(self._pick_out_color)
        tl.addWidget(self._btn_out_color)

        self._btn_preview_clip = QPushButton("▶ Preview")
        self._btn_preview_clip.setObjectName("btn_create_clip")
        self._btn_preview_clip.setEnabled(False)
        self._btn_preview_clip.setToolTip("Previsualizar el clip seleccionado (P)")
        self._btn_preview_clip.clicked.connect(self._preview_clip)
        tl.addWidget(self._btn_preview_clip)

        self._btn_create = QPushButton("＋ Crear Clip")
        self._btn_create.setObjectName("btn_create_clip")
        self._btn_create.setEnabled(False)
        self._btn_create.clicked.connect(self._create_clip)
        tl.addWidget(self._btn_create)

        layout.addWidget(tools)

        # Regla
        ruler = QWidget()
        ruler.setObjectName("timeline_ruler")
        rl = QHBoxLayout(ruler)
        rl.setContentsMargins(88, 0, 8, 0)
        self._ruler_lbl = QLabel("00:00   00:30   01:00   01:30   02:00   02:30   03:00")
        self._ruler_lbl.setStyleSheet("color:#333333; font-size:10px; font-family:'Courier New';")
        rl.addWidget(self._ruler_lbl)
        layout.addWidget(ruler)

        # Tracks
        tracks = QWidget()
        tracks_l = QHBoxLayout(tracks)
        tracks_l.setContentsMargins(0, 0, 0, 0)
        tracks_l.setSpacing(0)

        track_lbl = QWidget()
        track_lbl.setObjectName("track_label")
        track_lbl.setFixedWidth(80)
        tll = QVBoxLayout(track_lbl)
        tll.setAlignment(Qt.AlignCenter)
        lbl_main = QLabel("Principal")
        lbl_main.setStyleSheet("color:#444444; font-size:10px;")
        tll.addWidget(lbl_main)
        tracks_l.addWidget(track_lbl)

        track_content = QWidget()
        track_content.setObjectName("track_area")
        tc = QVBoxLayout(track_content)
        tc.setContentsMargins(0, 0, 0, 0)
        tc.setSpacing(0)

        self._waveform = WaveformWidget()
        self._waveform.seek_requested.connect(self._on_waveform_seek)
        tc.addWidget(self._waveform, stretch=1)

        tracks_l.addWidget(track_content, stretch=1)
        layout.addWidget(tracks, stretch=1)

        # Bottom bar
        bottom = QWidget()
        bottom.setStyleSheet("background:#0a0a0a; border-top:1px solid #1a1a1a;")
        bl = QHBoxLayout(bottom)
        bl.setContentsMargins(88, 4, 12, 4)
        bl.setSpacing(8)

        self._subs_options = SubtitlesOptions()
        bl.addWidget(self._subs_options)
        bl.addStretch()

        for icon in ["−", "+"]:
            btn = QPushButton(icon)
            btn.setFixedSize(24, 24)
            btn.setStyleSheet("""
                QPushButton { background:#1a1a1a; color:#666; border:1px solid #222;
                    border-radius:4px; font-size:13px; font-weight:700; }
                QPushButton:hover { color:#fff; }
            """)
            bl.addWidget(btn)

        layout.addWidget(bottom)

        # Slider
        slider_row = QWidget()
        slider_row.setStyleSheet("background:#080808; border-top:1px solid #111;")
        sl = QHBoxLayout(slider_row)
        sl.setContentsMargins(88, 3, 12, 5)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setObjectName("timeline_slider")
        self._slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._slider.sliderMoved.connect(self._on_slider_moved)
        self._slider.sliderPressed.connect(lambda: setattr(self, '_slider_dragging', True))
        self._slider.sliderReleased.connect(self._on_slider_released)
        sl.addWidget(self._slider)
        layout.addWidget(slider_row)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(3)
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
        QShortcut(QKeySequence("P"),      self, self._preview_clip)
        QShortcut(QKeySequence("R"),      self, self._reset_in_out)        # #12
        QShortcut(QKeySequence("A"),      self, self._select_all_video)    # #16
        QShortcut(QKeySequence("L"),      self, self._toggle_loop)         # #8
        QShortcut(QKeySequence("S"),      self, self._screenshot)          # #6
        QShortcut(QKeySequence("Home"),   self, lambda: self._goto_frame(0))          # #19
        QShortcut(QKeySequence("End"),    self, lambda: self._goto_frame(self._total_frames - 1))  # #19
        QShortcut(QKeySequence(","),      self, lambda: self._skip_frames(-1))  # frame a frame
        QShortcut(QKeySequence("."),      self, lambda: self._skip_frames(1))   # frame a frame

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_overlay_label'):
            w = self._video_widget.width()
            h = self._video_widget.height()
            self._overlay_label.setGeometry(0, (h - 40) // 2, w, 40)

    # ── Drag & Drop (#1) ──────────────────────────────────────────────
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            ext = os.path.splitext(path)[1].lower()
            if ext in ('.mp4', '.avi', '.mkv', '.mov', '.flv', '.webm'):
                if path not in self._media_files:
                    self._media_files.append(path)
                    self._media_list.addItem(f"  🎬  {os.path.basename(path)}")
                self._open_media(path)
                break

    # ══════════════════════════════════════════════════════════════════
    # VIDEO
    # ══════════════════════════════════════════════════════════════════

    @pyqtSlot()
    def _load_video(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Importar Videos", os.path.expanduser("~"),
            "Videos (*.mp4 *.avi *.mkv *.mov *.flv *.webm)"
        )
        if not files:
            return
        for file in files:
            if file not in self._media_files:
                self._media_files.append(file)
                self._media_list.addItem(f"  🎬  {os.path.basename(file)}")
        if not self._source_path:
            self._media_list.setCurrentRow(0)
            self._open_media(self._media_files[0])

    def _on_media_double_clicked(self, item):
        row = self._media_list.row(item)
        if 0 <= row < len(self._media_files):
            self._open_media(self._media_files[row])

    def _remove_media(self):
        row = self._media_list.currentRow()
        if row < 0:
            return
        file = self._media_files[row]
        self._media_list.takeItem(row)
        self._media_files.pop(row)
        if file == self._source_path:
            self._player.stop()
            self._source_path = ""
            self._is_playing  = False
            self._btn_play.setText("▶")
            self._overlay_label.show()
            self._slider.setValue(0)
            self._waveform.set_total_frames(0)
            self._timecode_lbl.setText("00:00:00.00")
            self._btn_export_top.setEnabled(False)
            self._highlights_panel.set_ready(False)

    def _open_media(self, file: str):
        self._player.stop()
        self._is_playing = False
        self._btn_play.setText("▶")
        self._in_frame   = -1
        self._out_frame  = -1

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
        self._project_name.setText(name)
        self._timecode_total.setText(f"/ {secs_to_tc(dur)}")
        self._overlay_label.hide()

        # Guardar último video (#3)
        self._settings.setValue("last_video", file)

        # Mostrar FPS y resolución (#18)
        self._video_info_lbl.setText(f"{self._fps:.0f}fps")

        self._status.showMessage(
            f"{name}  |  {dur/60:.1f} min  |  {self._fps:.2f} fps  |  {self._total_frames:,} frames"
        )

        self._player.play()
        self._player.set_volume(self._vol_slider.value())
        self._is_playing = True
        self._btn_play.setText("⏸")

        if self._detector and self._detector.isRunning():
            self._detector.quit()
            self._detector.wait()

        if self._ffmpeg_path:
            self._detector = HighlightDetector(self._ffmpeg_path, file)
            self._detector.finished.connect(self._on_all_highlights_found)
            self._highlights_panel.set_detector(self._detector)
            self._highlights_panel.set_ready(True)
        else:
            self._highlights_panel.set_ready(False)

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
        self._timecode_lbl.setText(secs_to_tc(frame / (self._fps or 30)))

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
        self._btn_preview_clip.setEnabled(valid and bool(self._source_path))
        self._btn_export_top.setEnabled(valid and bool(self._source_path))

        # Tamaño estimado (#13) ~5 Mbps para mp4
        if valid:
            dur = (self._out_frame - self._in_frame) / (self._fps or 30)
            est_mb = dur * 5 * 1024 / 8 / 1024  # 5 Mbps estimado
            self._size_lbl.setText(f"~{est_mb:.0f} MB")
        else:
            self._size_lbl.setText("")

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
        self._update_clips_counter()

    def _update_clips_counter(self):
        n = len(self._clips)
        self._clips_counter.setText(f"{n} clip{'s' if n != 1 else ''}")
        color = "#7c4dff" if n > 0 else "#444444"
        self._clips_counter.setStyleSheet(
            f"color:{color}; font-size:11px; font-weight:600; "
            "background:#1a1a1a; border:1px solid #2a2a2a; "
            "border-radius:10px; padding:3px 10px;"
        )
        # Duración total (#10)
        if n > 0:
            total = sum(c.duration_seconds for c in self._clips)
            m = int(total // 60); s = total % 60
            self._total_dur_lbl.setText(f"Duración total: {m}:{s:05.2f}")
        else:
            self._total_dur_lbl.setText("Duración total: —")

    def _preview_clip(self):
        if not (self._in_frame >= 0 and self._out_frame > self._in_frame):
            return
        self._preview_out_frame = self._out_frame
        self._player.seek(self._in_frame)
        self._slider.setValue(self._in_frame)
        self._player.play()
        self._is_playing = True
        self._btn_play.setText("⏸")
        self._status.showMessage(
            f"▶ Previsualizando clip · {secs_to_tc(self._in_frame/(self._fps or 30))} → "
            f"{secs_to_tc(self._out_frame/(self._fps or 30))}"
        )

    # ── Nuevas features ───────────────────────────────────────────────

    # #6 - Captura de pantalla
    def _screenshot(self):
        if not self._source_path:
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar captura", 
            os.path.join(self._default_output_dir, f"frame_{self._current_frame}.png"),
            "Imagen (*.png)"
        )
        if not save_path:
            return
        try:
            import cv2
            cap = cv2.VideoCapture(self._source_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, self._current_frame)
            ret, frame = cap.read()
            cap.release()
            if ret:
                cv2.imwrite(save_path, frame)
                self._status.showMessage(f"✓ Captura guardada: {os.path.basename(save_path)}")
        except Exception as e:
            self._status.showMessage(f"⚠ Error captura: {e}")

    # #7 - Carpeta de salida
    def _set_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Carpeta de salida por defecto", self._default_output_dir)
        if d:
            self._default_output_dir = d
            self._settings.setValue("output_dir", d)
            self._status.showMessage(f"✓ Carpeta de salida: {d}")

    # #8 - Loop
    def _toggle_loop(self):
        self._btn_loop.setChecked(not self._btn_loop.isChecked())

    # #11 - Copiar timecode
    def _copy_timecode(self):
        tc = self._timecode_lbl.text()
        QApplication.clipboard().setText(tc)
        self._status.showMessage(f"✓ Timecode copiado: {tc}", 2000)

    # #12 - Resetear IN/OUT
    def _reset_in_out(self):
        self._in_frame  = -1
        self._out_frame = -1
        self._waveform.set_in_frame(-1)
        self._waveform.set_out_frame(-1)
        self._update_in_out_display()
        self._status.showMessage("IN/OUT reseteados")

    # #15 - Duplicar clip
    def _duplicate_clip(self):
        row = self._clips_list.currentRow()
        if row < 0 or row >= len(self._clips):
            return
        orig = self._clips[row]
        from core.clip_model import Clip
        dup = Clip(
            source_path=orig.source_path,
            in_frame=orig.in_frame,
            out_frame=orig.out_frame,
            fps=orig.fps,
            label=f"{orig.display_name()} (copia)",
            export_preset=orig.export_preset,
        )
        self._clips.append(dup)
        item = QListWidgetItem(f"  {dup.display_name()}\n  ⏱ {dup.duration_str}")
        item.setData(Qt.UserRole, dup.id)
        self._clips_list.addItem(item)
        self._update_clips_counter()
        self._status.showMessage(f"✓ Clip duplicado")

    # #14 - Ordenar clips
    def _sort_clips(self, by: str):
        if by == "name":
            self._clips.sort(key=lambda c: c.display_name().lower())
        elif by == "duration":
            self._clips.sort(key=lambda c: c.duration_seconds, reverse=True)
        self._clips_list.clear()
        for c in self._clips:
            item = QListWidgetItem(f"  {c.display_name()}\n  ⏱ {c.duration_str}")
            item.setData(Qt.UserRole, c.id)
            self._clips_list.addItem(item)
        self._status.showMessage(f"✓ Clips ordenados por {by}")

    # #4 - Renombrar clip con doble clic
    def _rename_clip(self, item: QListWidgetItem):
        clip_id = item.data(Qt.UserRole)
        clip = next((c for c in self._clips if c.id == clip_id), None)
        if not clip:
            return
        new_name, ok = QInputDialog.getText(
            self, "Renombrar clip", "Nuevo nombre:", text=clip.label or clip.display_name()
        )
        if ok and new_name.strip():
            clip.label = new_name.strip()
            item.setText(f"  {clip.display_name()}\n  ⏱ {clip.duration_str}")
            self._status.showMessage(f"✓ Renombrado: {clip.display_name()}")

    # #16 - Seleccionar todo el video
    def _select_all_video(self):
        if not self._source_path or self._total_frames <= 0:
            return
        self._in_frame  = 0
        self._out_frame = self._total_frames - 1
        self._waveform.set_in_frame(0)
        self._waveform.set_out_frame(self._total_frames - 1)
        self._update_in_out_display()

    # #17 - Volumen con rueda del mouse
    def _vol_wheel(self, event):
        delta = event.angleDelta().y()
        new_val = max(0, min(100, self._vol_slider.value() + (5 if delta > 0 else -5)))
        self._vol_slider.setValue(new_val)

    # #19 - Ir a frame específico
    def _goto_frame(self, frame: int):
        if not self._source_path:
            return
        frame = max(0, min(frame, self._total_frames - 1))
        self._player.seek(frame)
        self._slider.setValue(frame)
        self._update_timecode(frame)

    # Frame a frame (#11 extra)
    def _skip_frames(self, n: int):
        if not self._source_path:
            return
        new_frame = max(0, min(self._current_frame + n, self._total_frames - 1))
        self._player.seek(new_frame)
        self._slider.setValue(new_frame)

    # #20 - Color personalizable IN/OUT
    def _pick_in_color(self):
        color = QColorDialog.getColor(QColor(self._in_color), self, "Color marcador IN")
        if color.isValid():
            self._in_color = color.name()
            self._btn_in_color.setStyleSheet(f"background:{self._in_color}; border-radius:8px; border:none;")

    def _pick_out_color(self):
        color = QColorDialog.getColor(QColor(self._out_color), self, "Color marcador OUT")
        if color.isValid():
            self._out_color = color.name()
            self._btn_out_color.setStyleSheet(f"background:{self._out_color}; border-radius:8px; border:none;")

    def _delete_clip(self):
        row = self._clips_list.currentRow()
        if row < 0:
            return
        item = self._clips_list.takeItem(row)
        clip_id = item.data(Qt.UserRole)
        self._clips = [c for c in self._clips if c.id != clip_id]
        self._btn_delete.setEnabled(self._clips_list.count() > 0)
        self._update_clips_counter()

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
            self, "Exportar Clip",
            os.path.join(self._default_output_dir, f"clip.{ext}"),
            f"Video (*.{ext})"
        )
        if not save_path:
            return

        self._btn_export_top.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)

        if self._subs_options.enabled:
            self._status.showMessage("Exportando con subtítulos…")
            self._export_worker = ExportWithSubtitlesWorker(
                ffmpeg_path=self._ffmpeg_path,
                source=self._source_path,
                start_s=in_s, end_s=out_s,
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
            combined_vf = self._get_ffmpeg_filters(preset["vf"])
            audio_args  = self._get_audio_filters()
            extra = list(preset["extra"])
            if audio_args:
                extra = audio_args + extra
            # Velocidad en audio
            spd = getattr(self, '_speed_slider', None)
            if spd and abs(spd.value()/10 - 1.0) > 0.01:
                atempo = spd.value() / 10.0
                atempo = max(0.5, min(atempo, 2.0))
                af = f"atempo={atempo:.2f}"
                if audio_args:
                    extra[extra.index(audio_args[-1])] += f",{af}"
                else:
                    extra = ["-af", af] + extra
            self._export_worker = ExportWorker(
                ffmpeg_path=self._ffmpeg_path,
                source=self._source_path,
                start_s=in_s, end_s=out_s,
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

        # Notificación de Windows (#2)
        if self._tray:
            self._tray.showMessage(
                "StreamerClipsAI",
                f"✓ Clip exportado: {os.path.basename(path)}",
                QSystemTrayIcon.Information, 4000
            )

        # Botón para abrir carpeta (#9)
        folder = os.path.dirname(path)
        reply = QMessageBox.question(
            self, "Exportación completada",
            f"✓ Guardado como:\n{os.path.basename(path)}\n\n¿Abrir carpeta?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            os.startfile(folder)

        if self.auth and self.auth.is_logged_in:
            fps = self._fps or 30
            dur = (self._out_frame - self._in_frame) / fps if self._out_frame > self._in_frame else 0
            label = self._clip_name_edit.text().strip() or os.path.basename(path)
            self.auth.save_clip(
                source_path=self._source_path, output_path=path,
                preset=self._combo_format.currentText(), duration=dur, label=label
            )
            if self._history_panel:
                self._history_panel.refresh()

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
        # Detener al llegar al out_frame durante preview
        if hasattr(self, '_preview_out_frame') and self._preview_out_frame > 0:
            if frame >= self._preview_out_frame:
                self._player.pause()
                self._is_playing = False
                self._btn_play.setText("▶")
                self._preview_out_frame = 0
                self._status.showMessage("✓ Preview finalizado")
        # Loop del clip (#8)
        elif self._loop_clip and self._in_frame >= 0 and self._out_frame > self._in_frame:
            if frame >= self._out_frame:
                self._player.seek(self._in_frame)
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
        frame = int(seconds * (self._fps or 30))
        self._player.seek(frame)
        self._slider.setValue(frame)

    @pyqtSlot(object)
    def _on_highlight_add(self, highlight):
        fps = self._fps or 30
        clip = Clip(
            source_path=self._source_path,
            in_frame=int(highlight.start_sec * fps),
            out_frame=int(highlight.end_sec * fps),
            fps=fps,
            label=highlight.label(),
            export_preset=self._combo_format.currentText(),
        )
        self._clips.append(clip)
        item = QListWidgetItem(f"  {clip.display_name()}\n  ⏱ {clip.duration_str}")
        item.setData(Qt.UserRole, clip.id)
        self._clips_list.addItem(item)
        self._clips_list.setCurrentItem(item)
        self._btn_delete.setEnabled(True)
        self._status.showMessage(f"✓ Highlight agregado: {clip.display_name()}")

    @pyqtSlot(list)
    def _on_all_highlights_found(self, highlights: list):
        if not highlights:
            return
        fps = self._fps or 30
        added = 0
        for h in highlights:
            clip = Clip(
                source_path=self._source_path,
                in_frame=int(h.start_sec * fps),
                out_frame=int(h.end_sec * fps),
                fps=fps,
                label=h.label(),
                export_preset=self._combo_format.currentText(),
            )
            self._clips.append(clip)
            item = QListWidgetItem(f"  {clip.display_name()}\n  ⏱ {clip.duration_str}")
            item.setData(Qt.UserRole, clip.id)
            self._clips_list.addItem(item)
            added += 1
        if added > 0:
            self._btn_delete.setEnabled(True)
            self._clips_list.setCurrentRow(self._clips_list.count() - added)
            self._status.showMessage(f"🤖 IA encontró {added} highlights")

    # ══════════════════════════════════════════════════════════════════
    # USUARIO / NAVEGACIÓN
    # ══════════════════════════════════════════════════════════════════

    # ── Métodos de transformación / audio / velocidad / ajustar ──────

    def _on_transform_changed(self):
        pass  # Preview en tiempo real requeriría VLC filters (futuro)

    def _reset_transform(self):
        self._scale_slider.setValue(100)
        self._pos_x.setValue(0)
        self._pos_y.setValue(0)
        self._rotation_slider.setValue(0)

    def _reset_audio(self):
        self._audio_vol_slider.setValue(0)
        self._fade_in_slider.setValue(0)
        self._fade_out_slider.setValue(0)

    def _reset_adjust(self):
        for attr in ["_adj_brightness", "_adj_contrast", "_adj_saturation",
                     "_adj_sharpness", "_adj_temp", "_adj_tint"]:
            s = getattr(self, attr, None)
            if s:
                s.setValue(0)

    def _update_speed_duration(self, speed_val: int):
        speed = speed_val / 10.0
        if self._in_frame >= 0 and self._out_frame > self._in_frame:
            dur = (self._out_frame - self._in_frame) / (self._fps or 30)
            new_dur = dur / speed
            m = int(new_dur // 60); s = new_dur % 60
            self._speed_dur_lbl.setText(f"Duración estimada: {m}:{s:04.1f}s")
        else:
            self._speed_dur_lbl.setText("Duración estimada: —")

    def _get_ffmpeg_filters(self, base_vf: str) -> str:
        """Construye el filtro de video combinando preset + ajustes del usuario."""
        filters = []

        # Velocidad
        speed = getattr(self, '_speed_slider', None)
        spd = speed.value() / 10.0 if speed else 1.0
        if abs(spd - 1.0) > 0.01:
            filters.append(f"setpts={1/spd:.3f}*PTS")

        # Escala/posición/rotación
        scale = getattr(self, '_scale_slider', None)
        rot   = getattr(self, '_rotation_slider', None)
        if scale and scale.value() != 100:
            s = scale.value() / 100.0
            filters.append(f"scale=iw*{s:.2f}:ih*{s:.2f}")
        if rot and rot.value() != 0:
            filters.append(f"rotate={rot.value()}*PI/180")

        # Ajustes de color
        eq_parts = []
        bright = getattr(self, '_adj_brightness', None)
        contr  = getattr(self, '_adj_contrast', None)
        sat    = getattr(self, '_adj_saturation', None)
        if bright and bright.value() != 0:
            eq_parts.append(f"brightness={bright.value()/100:.2f}")
        if contr and contr.value() != 0:
            eq_parts.append(f"contrast={1 + contr.value()/100:.2f}")
        if sat and sat.value() != 0:
            eq_parts.append(f"saturation={1 + sat.value()/100:.2f}")
        if eq_parts:
            filters.append(f"eq={':'.join(eq_parts)}")

        # Nitidez
        sharp = getattr(self, '_adj_sharpness', None)
        if sharp and sharp.value() > 0:
            filters.append(f"unsharp=5:5:{sharp.value()/50:.1f}")

        # Preset base
        if base_vf:
            filters.append(base_vf)

        return ",".join(filters) if filters else base_vf or ""

    def _get_audio_filters(self) -> list:
        """Retorna filtros de audio FFmpeg según configuración."""
        args = []
        vol = getattr(self, '_audio_vol_slider', None)
        if vol and vol.value() != 0:
            db = vol.value()
            factor = 10 ** (db / 20)
            args += ["-af", f"volume={factor:.3f}"]
        return args

    # ── Aspect ratio del preview según formato ────────────────────────
    def _on_format_changed(self, preset_name: str):
        """Cambia el aspect ratio del video_widget según el formato."""
        is_vertical = "9:16" in preset_name
        container = self._video_widget.parent()
        if is_vertical:
            self._video_widget.setMaximumWidth(int(self._video_widget.height() * 9 / 16) + 1)
        else:
            self._video_widget.setMaximumWidth(16777215)  # sin límite

    def _show_about(self):
        from ui.about_dialog import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec_()

    def _go_back(self):
        if self._back_callback:
            self._back_callback()
        else:
            parent = self.parent()
            if parent and hasattr(parent, 'setCurrentIndex'):
                parent.resize(1100, 700)
                parent.setCurrentIndex(1)

    def on_user_logged_in(self, user):
        self._profile_widget.set_user(user)
        if self._history_panel:
            self._history_panel.refresh()

    def _do_logout(self):
        if self.auth:
            self.auth.logout()
        self._profile_widget.hide()
        parent = self.parent()
        if parent and hasattr(parent, 'setCurrentIndex'):
            parent.resize(420, 580)
            parent.setMinimumSize(400, 500)
            parent.setCurrentIndex(0)
            parent.setWindowTitle("StreamerClipsAI")

    def closeEvent(self, event):
        if self._detector and self._detector.isRunning():
            self._detector.quit()
            self._detector.wait()
        self._player.cleanup()
        event.accept()
