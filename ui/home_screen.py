"""
ui/home_screen.py
Pantalla de inicio estilo CapCut.
Aparece después del login con botón "Crear proyecto" e historial de clips.
"""
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QGridLayout,
    QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import (
    QPixmap, QColor, QPainter, QPainterPath,
    QLinearGradient, QBrush, QFont
)
from ui.profile_widget import ProfileWidget


HOME_STYLE = """
QWidget#home_root {
    background-color: #0f0f0f;
}

QWidget#topbar_home {
    background-color: #111111;
    border-bottom: 1px solid #1e1e1e;
    min-height: 52px;
    max-height: 52px;
}

QLabel#app_title {
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.5px;
}

QLabel#app_subtitle {
    font-size: 10px;
    color: #7c4dff;
    font-weight: 600;
    letter-spacing: 2px;
}

QLabel#section_title {
    font-size: 13px;
    font-weight: 700;
    color: #888888;
    letter-spacing: 2px;
    padding: 0px 4px;
}

QLabel#clip_name {
    font-size: 12px;
    font-weight: 600;
    color: #cccccc;
    background: transparent;
}

QLabel#clip_meta {
    font-size: 10px;
    color: #555555;
    background: transparent;
    font-family: 'Courier New';
}

QWidget#clip_card {
    background: #161616;
    border: 1px solid #222222;
    border-radius: 10px;
}

QWidget#clip_card:hover {
    border-color: #7c4dff;
    background: #1a1a2a;
}

QPushButton#btn_new_project {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1a0a3a, stop:1 #0a1a3a);
    color: #ffffff;
    border: 2px dashed #3a2a6a;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 700;
    padding: 0px;
}

QPushButton#btn_new_project:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #2a1a5a, stop:1 #1a2a5a);
    border-color: #7c4dff;
}

QPushButton#btn_open_editor {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5c2dff, stop:1 #7c4dff);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
    padding: 10px 24px;
}

QPushButton#btn_open_editor:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c4dff, stop:1 #9c6dff);
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: #111111; width: 5px; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #333333; border-radius: 3px; min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def fmt_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%d/%m/%Y")
    except:
        return ""


def fmt_duration(secs: float) -> str:
    m = int(secs // 60)
    s = int(secs % 60)
    return f"{m}:{s:02d}"


class ClipCard(QWidget):
    """Tarjeta de un clip del historial."""
    clicked = pyqtSignal(object)

    def __init__(self, clip_history, parent=None):
        super().__init__(parent)
        self.clip = clip_history
        self.setObjectName("clip_card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(180, 140)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        # Miniatura / thumbnail
        thumb = QLabel()
        thumb.setFixedHeight(80)
        thumb.setAlignment(Qt.AlignCenter)
        thumb.setStyleSheet("background:#0a0a0a; border-radius:6px; border:none;")

        # Intentar cargar thumbnail del video
        exists = os.path.exists(self.clip.output_path)
        if exists:
            thumb.setText("🎬")
            thumb.setStyleSheet(
                "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                "stop:0 #1a0a3a, stop:1 #0a1a3a);"
                "color:#7c4dff; font-size:28px; border-radius:6px; border:none;"
            )
        else:
            thumb.setText("✗")
            thumb.setStyleSheet(
                "background:#1a0a0a; color:#3a1a1a; font-size:28px;"
                "border-radius:6px; border:none;"
            )
        layout.addWidget(thumb)

        # Nombre
        name = QLabel(self.clip.label or os.path.basename(self.clip.output_path))
        name.setObjectName("clip_name")
        name.setWordWrap(False)
        name.setMaximumWidth(160)
        # Truncar texto largo
        fm = name.fontMetrics()
        text = name.text()
        if fm.width(text) > 155:
            text = fm.elidedText(text, Qt.ElideRight, 155)
            name.setText(text)
        layout.addWidget(name)

        # Meta
        dur = fmt_duration(self.clip.duration)
        date = fmt_date(self.clip.created_at)
        meta = QLabel(f"⏱ {dur}  ·  {date}")
        meta.setObjectName("clip_meta")
        layout.addWidget(meta)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.clip)


class HomeScreen(QWidget):
    """
    Pantalla de inicio estilo CapCut.
    Emite open_editor cuando el usuario quiere crear/abrir un proyecto.
    """
    open_editor   = pyqtSignal()
    logout_requested = pyqtSignal()

    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth = auth_manager
        self.setObjectName("home_root")
        self.setStyleSheet(HOME_STYLE)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Topbar ──
        root.addWidget(self._build_topbar())

        # ── Contenido scrolleable ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:#0f0f0f; border:none;")

        content = QWidget()
        content.setStyleSheet("background:#0f0f0f;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 36, 40, 40)
        content_layout.setSpacing(32)

        # ── Botón crear proyecto ──
        content_layout.addWidget(self._build_create_section())

        # ── Historial ──
        content_layout.addWidget(self._build_history_section())
        content_layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

    def _build_topbar(self):
        bar = QWidget()
        bar.setObjectName("topbar_home")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(8)

        title = QLabel("StreamerClips")
        title.setObjectName("app_title")
        sub = QLabel("AI")
        sub.setObjectName("app_subtitle")
        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addStretch()

        self._profile_widget = ProfileWidget()
        self._profile_widget.logout_requested.connect(self.logout_requested)
        layout.addWidget(self._profile_widget)

        return bar

    def _build_create_section(self):
        section = QWidget()
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Botón grande crear proyecto
        btn_new = QPushButton()
        btn_new.setObjectName("btn_new_project")
        btn_new.setFixedSize(200, 130)
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.clicked.connect(self.open_editor)

        # Layout interno del botón
        btn_layout = QVBoxLayout(btn_new)
        btn_layout.setAlignment(Qt.AlignCenter)
        icon = QLabel("＋")
        icon.setStyleSheet("font-size:32px; color:#7c4dff; background:transparent; border:none;")
        icon.setAlignment(Qt.AlignCenter)
        text = QLabel("Crear proyecto")
        text.setStyleSheet("font-size:13px; font-weight:700; color:#aaaaaa; background:transparent; border:none;")
        text.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(icon)
        btn_layout.addWidget(text)

        layout.addWidget(btn_new)

        # Card de herramientas IA
        ai_card = QWidget()
        ai_card.setFixedSize(200, 130)
        ai_card.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #0a1a2a, stop:1 #1a0a3a);
            border: 1px solid #1e2a3a;
            border-radius: 12px;
        """)
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setAlignment(Qt.AlignCenter)
        ai_icon = QLabel("🤖")
        ai_icon.setStyleSheet("font-size:28px; background:transparent; border:none;")
        ai_icon.setAlignment(Qt.AlignCenter)
        ai_text = QLabel("Highlights IA")
        ai_text.setStyleSheet("font-size:13px; font-weight:700; color:#7c4dff; background:transparent; border:none;")
        ai_text.setAlignment(Qt.AlignCenter)
        ai_sub = QLabel("Detección automática")
        ai_sub.setStyleSheet("font-size:10px; color:#44445a; background:transparent; border:none;")
        ai_sub.setAlignment(Qt.AlignCenter)
        ai_layout.addWidget(ai_icon)
        ai_layout.addWidget(ai_text)
        ai_layout.addWidget(ai_sub)
        layout.addWidget(ai_card)

        # Card subtítulos
        sub_card = QWidget()
        sub_card.setFixedSize(200, 130)
        sub_card.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #0a1a0a, stop:1 #0a2a1a);
            border: 1px solid #1a2a1e;
            border-radius: 12px;
        """)
        sub_layout = QVBoxLayout(sub_card)
        sub_layout.setAlignment(Qt.AlignCenter)
        sub_icon = QLabel("🗣")
        sub_icon.setStyleSheet("font-size:28px; background:transparent; border:none;")
        sub_icon.setAlignment(Qt.AlignCenter)
        sub_text = QLabel("Subtítulos IA")
        sub_text.setStyleSheet("font-size:13px; font-weight:700; color:#00c853; background:transparent; border:none;")
        sub_text.setAlignment(Qt.AlignCenter)
        sub_sub = QLabel("Whisper automático")
        sub_sub.setStyleSheet("font-size:10px; color:#44445a; background:transparent; border:none;")
        sub_sub.setAlignment(Qt.AlignCenter)
        sub_layout.addWidget(sub_icon)
        sub_layout.addWidget(sub_text)
        sub_layout.addWidget(sub_sub)
        layout.addWidget(sub_card)

        layout.addStretch()
        return section

    def _build_history_section(self):
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Título sección
        title_row = QHBoxLayout()
        title = QLabel("PROYECTOS RECIENTES")
        title.setObjectName("section_title")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#1e1e1e;")
        layout.addWidget(sep)

        # Grid de clips
        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet("background:transparent;")
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(14)
        self._grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self._empty_lbl = QLabel("Aún no tienes clips exportados.\nCrea tu primer proyecto 🎬")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet("color:#333333; font-size:14px; padding:40px;")

        layout.addWidget(self._grid_widget)
        layout.addWidget(self._empty_lbl)

        return section

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def set_user(self, user):
        self._profile_widget.set_user(user)
        self.refresh_history()

    def refresh_history(self):
        """Recarga el historial de clips del usuario."""
        # Limpiar grid
        for i in reversed(range(self._grid_layout.count())):
            w = self._grid_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not self.auth or not self.auth.is_logged_in:
            self._empty_lbl.show()
            return

        clips = self.auth.get_clip_history()

        if not clips:
            self._empty_lbl.show()
            self._grid_widget.hide()
            return

        self._empty_lbl.hide()
        self._grid_widget.show()

        cols = 6
        for i, clip in enumerate(clips):
            card = ClipCard(clip)
            card.clicked.connect(self._on_clip_clicked)
            self._grid_layout.addWidget(card, i // cols, i % cols)

    def _on_clip_clicked(self, clip):
        """Abrir el editor al hacer clic en un clip del historial."""
        self.open_editor.emit()
