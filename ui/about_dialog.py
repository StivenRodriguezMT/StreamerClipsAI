"""
ui/about_dialog.py
Ventana "Acerca de" con créditos, redes sociales del creador y colaboradores.
"""
import webbrowser
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QBrush, QFont


ABOUT_STYLE = """
QDialog#about_dialog {
    background-color: #0a0a0f;
}

QWidget#card {
    background-color: #0f0f18;
    border-radius: 20px;
    border: 1px solid #1e1e35;
}

QLabel#app_logo {
    font-size: 28px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -1px;
    background: transparent;
}

QLabel#app_logo_ai {
    font-size: 28px;
    font-weight: 900;
    color: #7c4dff;
    background: transparent;
}

QLabel#version_lbl {
    font-size: 11px;
    color: #333355;
    letter-spacing: 3px;
    background: transparent;
}

QLabel#section_title {
    font-size: 10px;
    font-weight: 700;
    color: #333355;
    letter-spacing: 3px;
    background: transparent;
}

QLabel#person_name {
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
    background: transparent;
}

QLabel#person_role {
    font-size: 11px;
    color: #7c4dff;
    font-weight: 600;
    letter-spacing: 1px;
    background: transparent;
}

QWidget#person_card {
    background: #111118;
    border: 1px solid #1e1e35;
    border-radius: 14px;
}

QPushButton#btn_close {
    background: #1a1a2a;
    color: #555577;
    border: 1px solid #1e1e35;
    border-radius: 8px;
    padding: 8px 24px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton#btn_close:hover {
    background: #222235;
    color: #aaaacc;
    border-color: #7c4dff;
}

QFrame#divider {
    background: #1a1a2a;
    max-height: 1px;
    border: none;
}
"""


SOCIAL_BUTTONS = {
    "Instagram": {
        "icon": "📸",
        "color": "#e1306c",
        "bg": "#1a0a12",
        "border": "#3a1525",
    },
    "Kick": {
        "icon": "🟢",
        "color": "#53fc18",
        "bg": "#0a1a0a",
        "border": "#1a3a1a",
    },
    "TikTok": {
        "icon": "🎵",
        "color": "#00f2ea",
        "bg": "#0a1a1a",
        "border": "#1a3535",
    },
}


def _social_btn(platform: str, url: str) -> QPushButton:
    info = SOCIAL_BUTTONS.get(platform, {"icon": "🔗", "color": "#aaaaaa", "bg": "#1a1a1a", "border": "#2a2a2a"})
    btn = QPushButton(f"{info['icon']}  {platform}")
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {info['bg']};
            color: {info['color']};
            border: 1px solid {info['border']};
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 700;
        }}
        QPushButton:hover {{
            background: {info['border']};
            border-color: {info['color']};
        }}
    """)
    btn.clicked.connect(lambda: webbrowser.open(url))
    return btn


def _person_card(name: str, role: str, socials: list) -> QWidget:
    card = QWidget()
    card.setObjectName("person_card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)

    name_lbl = QLabel(name)
    name_lbl.setObjectName("person_name")
    layout.addWidget(name_lbl)

    role_lbl = QLabel(role)
    role_lbl.setObjectName("person_role")
    layout.addWidget(role_lbl)

    btns_row = QHBoxLayout()
    btns_row.setSpacing(6)
    for platform, url in socials:
        btns_row.addWidget(_social_btn(platform, url))
    btns_row.addStretch()
    layout.addLayout(btns_row)

    return card


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("about_dialog")
        self.setWindowTitle("Acerca de StreamerClipsAI")
        self.setStyleSheet(ABOUT_STYLE)
        self.setFixedWidth(480)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        card = QWidget()
        card.setObjectName("card")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(124, 77, 255, 100))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(0)

        # ── Logo ──
        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignCenter)
        logo_row.setSpacing(0)
        l1 = QLabel("StreamerClips")
        l1.setObjectName("app_logo")
        l2 = QLabel("AI")
        l2.setObjectName("app_logo_ai")
        logo_row.addWidget(l1)
        logo_row.addWidget(l2)
        layout.addLayout(logo_row)

        ver = QLabel("VERSIÓN 1.0.0  ·  HECHO CON ❤️ PARA STREAMERS")
        ver.setObjectName("version_lbl")
        ver.setAlignment(Qt.AlignCenter)
        layout.addWidget(ver)
        layout.addSpacing(24)

        # ── Divider ──
        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.HLine)
        layout.addWidget(div)
        layout.addSpacing(20)

        # ── Creador ──
        sec1 = QLabel("CREADOR")
        sec1.setObjectName("section_title")
        layout.addWidget(sec1)
        layout.addSpacing(8)

        layout.addWidget(_person_card(
            name="Stiven Rodríguez",
            role="CREADOR & DESARROLLADOR PRINCIPAL",
            socials=[
                ("Instagram", "https://www.instagram.com/stivenrodrguez/"),
                ("Kick",      "https://kick.com/stivenmts"),
                ("TikTok",    "https://www.tiktok.com/@stiven.mts"),
            ]
        ))

        layout.addSpacing(16)

        # ── Colaboradores ──
        sec2 = QLabel("COLABORADORES")
        sec2.setObjectName("section_title")
        layout.addWidget(sec2)
        layout.addSpacing(8)

        layout.addWidget(_person_card(
            name="Jhandexx",
            role="COLABORADOR",
            socials=[
                ("Instagram", "https://www.instagram.com/jhandexx_/"),
                ("Kick",      "https://kick.com/jhandexx"),
                ("TikTok",    "https://www.tiktok.com/@jhandexx"),
            ]
        ))

        layout.addSpacing(24)

        # ── Botón cerrar ──
        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btn_close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)

        root.addWidget(card)

    def mousePressEvent(self, event):
        """Cerrar al hacer clic fuera de la tarjeta."""
        self.accept()
