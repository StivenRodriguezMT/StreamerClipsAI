"""
ui/profile_widget.py
Widget de perfil de usuario interactivo estilo CapCut.
Muestra avatar, nombre de usuario e ID, con menú desplegable
para cambiar foto de perfil y cerrar sesión.
"""
import os
import shutil
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFileDialog, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint, QRect
from PyQt5.QtGui import (
    QPixmap, QColor, QPainter, QPainterPath, QBrush,
    QFont, QLinearGradient
)

AVATARS_DIR = os.path.join(os.path.expanduser("~"), ".streamerclipsai", "avatars")


def get_avatar_path(user_id: int) -> str:
    return os.path.join(AVATARS_DIR, f"avatar_{user_id}.png")


def make_circle_pixmap(source: QPixmap, size: int) -> QPixmap:
    """Recorta un QPixmap en círculo."""
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    scaled = source.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    # Centrar
    x = (scaled.width() - size) // 2
    y = (scaled.height() - size) // 2
    painter.drawPixmap(-x, -y, scaled)
    painter.end()
    return result


def make_initials_pixmap(username: str, size: int) -> QPixmap:
    """Genera un avatar con las iniciales del usuario."""
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)

    # Fondo degradado púrpura
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor("#7c4dff"))
    grad.setColorAt(1, QColor("#00e5ff"))
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.fillPath(path, QBrush(grad))

    # Iniciales
    initials = username[:2].upper() if username else "??"
    painter.setPen(QColor("#ffffff"))
    font = QFont("Segoe UI", max(8, size // 3), QFont.Bold)
    painter.setFont(font)
    painter.drawText(QRect(0, 0, size, size), Qt.AlignCenter, initials)
    painter.end()
    return result


class AvatarButton(QPushButton):
    """Botón circular con foto de perfil."""

    def __init__(self, size: int = 32, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self._pixmap = None

    def set_pixmap(self, pixmap: QPixmap):
        self._pixmap = make_circle_pixmap(pixmap, self._size)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._pixmap:
            painter.drawPixmap(0, 0, self._pixmap)
        else:
            # Placeholder gris
            path = QPainterPath()
            path.addEllipse(0, 0, self._size, self._size)
            painter.fillPath(path, QBrush(QColor("#333333")))

        # Borde púrpura sutil
        painter.setPen(QColor("#7c4dff"))
        painter.drawEllipse(1, 1, self._size - 2, self._size - 2)
        painter.end()


class ProfileDropdown(QWidget):
    """Menú desplegable del perfil."""

    change_photo_requested = pyqtSignal()
    logout_requested       = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        card = QWidget()
        card.setObjectName("profile_dropdown")
        card.setStyleSheet("""
            QWidget#profile_dropdown {
                background: #161616;
                border: 1px solid #2a2a2a;
                border-radius: 12px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 8)
        card_layout.setSpacing(0)

        # Header con avatar grande
        header = QWidget()
        header.setStyleSheet("background: #111111; border-radius: 12px 12px 0 0;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 14, 16, 14)
        h_lay.setSpacing(12)

        self._avatar_large = AvatarButton(size=48)
        self._avatar_large.setEnabled(False)
        h_lay.addWidget(self._avatar_large)

        info = QVBoxLayout()
        info.setSpacing(2)
        self._name_lbl = QLabel("")
        self._name_lbl.setStyleSheet("color:#ffffff; font-size:14px; font-weight:700; background:transparent;")
        self._id_lbl = QLabel("")
        self._id_lbl.setStyleSheet("color:#555566; font-size:11px; font-family:'Courier New'; background:transparent;")
        self._email_lbl = QLabel("")
        self._email_lbl.setStyleSheet("color:#44445a; font-size:11px; background:transparent;")
        info.addWidget(self._name_lbl)
        info.addWidget(self._id_lbl)
        info.addWidget(self._email_lbl)
        h_lay.addLayout(info)
        card_layout.addWidget(header)

        # Separador
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #222222;")
        card_layout.addWidget(sep)
        card_layout.addSpacing(4)

        # Botón cambiar foto
        btn_photo = self._menu_btn("🖼  Cambiar foto de perfil")
        btn_photo.clicked.connect(self.change_photo_requested)
        card_layout.addWidget(btn_photo)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #1e1e1e; margin: 4px 0;")
        card_layout.addWidget(sep2)

        # Botón cerrar sesión
        btn_logout = self._menu_btn("↩  Cerrar sesión")
        btn_logout.setStyleSheet(btn_logout.styleSheet() + "color: #ff5555;")
        btn_logout.clicked.connect(self.logout_requested)
        card_layout.addWidget(btn_logout)

        layout.addWidget(card)
        self.setFixedWidth(260)

    def _menu_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #aaaaaa;
                border: none;
                border-radius: 0;
                padding: 9px 18px;
                font-size: 12px;
                font-weight: 600;
                text-align: left;
            }
            QPushButton:hover {
                background: #1e1e1e;
                color: #ffffff;
            }
        """)
        return btn

    def update_user(self, user, pixmap: QPixmap = None):
        self._name_lbl.setText(user.username)
        self._id_lbl.setText(f"ID: {user.id:08d}")
        self._email_lbl.setText(user.email)
        if pixmap:
            self._avatar_large.set_pixmap(pixmap)
        else:
            pm = make_initials_pixmap(user.username, 48)
            self._avatar_large.set_pixmap(pm)


class ProfileWidget(QWidget):
    """
    Widget completo de perfil para la topbar.
    Muestra avatar pequeño + nombre + menú desplegable.
    """
    logout_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._user = None
        self._avatar_pixmap = None
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Avatar pequeño (botón)
        self._avatar_btn = AvatarButton(size=32)
        self._avatar_btn.setCursor(Qt.PointingHandCursor)
        self._avatar_btn.clicked.connect(self._toggle_dropdown)
        layout.addWidget(self._avatar_btn)

        # Nombre + ID
        info = QVBoxLayout()
        info.setSpacing(0)
        self._name_lbl = QLabel("")
        self._name_lbl.setStyleSheet(
            "color:#dddddd; font-size:12px; font-weight:700; background:transparent;"
        )
        self._id_lbl = QLabel("")
        self._id_lbl.setStyleSheet(
            "color:#44445a; font-size:10px; font-family:'Courier New'; background:transparent;"
        )
        info.addWidget(self._name_lbl)
        info.addWidget(self._id_lbl)
        layout.addLayout(info)

        # Flecha
        self._arrow = QLabel("▾")
        self._arrow.setStyleSheet("color:#44445a; font-size:12px; background:transparent;")
        layout.addWidget(self._arrow)

        # Dropdown
        self._dropdown = ProfileDropdown()
        self._dropdown.change_photo_requested.connect(self._change_photo)
        self._dropdown.logout_requested.connect(self.logout_requested)

        self.hide()

    def set_user(self, user):
        self._user = user
        self._name_lbl.setText(user.username)
        self._id_lbl.setText(f"ID #{user.id:08d}")

        # Cargar avatar si existe
        avatar_path = get_avatar_path(user.id)
        if os.path.exists(avatar_path):
            pm = QPixmap(avatar_path)
            self._set_avatar(pm)
        else:
            pm = make_initials_pixmap(user.username, 64)
            self._set_avatar(pm)

        self._dropdown.update_user(user, self._avatar_pixmap)
        self.show()

    def _set_avatar(self, pixmap: QPixmap):
        self._avatar_pixmap = pixmap
        self._avatar_btn.set_pixmap(pixmap)

    def _toggle_dropdown(self):
        if self._dropdown.isVisible():
            self._dropdown.hide()
            return
        # Posicionar debajo del botón
        pos = self._avatar_btn.mapToGlobal(QPoint(0, self._avatar_btn.height() + 6))
        # Ajustar para que no salga de la pantalla
        pos.setX(pos.x() - 220)
        self._dropdown.move(pos)
        self._dropdown.show()

    def _change_photo(self):
        self._dropdown.hide()
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar foto de perfil",
            os.path.expanduser("~"),
            "Imágenes (*.png *.jpg *.jpeg *.webp)"
        )
        if not path or not self._user:
            return

        os.makedirs(AVATARS_DIR, exist_ok=True)
        dest = get_avatar_path(self._user.id)
        shutil.copy2(path, dest)

        pm = QPixmap(dest)
        self._set_avatar(pm)
        self._dropdown.update_user(self._user, pm)
