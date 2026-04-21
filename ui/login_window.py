"""
ui/login_window.py
Pantalla de login y registro para StreamerClipsAI.
Diseño oscuro estilo streamer con animaciones sutiles.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QStackedWidget,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter, QBrush


LOGIN_STYLE = """
QWidget#login_root {
    background-color: #0a0a0f;
}

QWidget#card {
    background-color: #111118;
    border-radius: 16px;
    border: 1px solid #1e1e2e;
}

QLabel#app_logo {
    font-size: 32px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -1px;
}

QLabel#app_logo_ai {
    font-size: 32px;
    font-weight: 900;
    color: #7c4dff;
}

QLabel#tagline {
    font-size: 12px;
    color: #44445a;
    letter-spacing: 3px;
}

QLabel#tab_title {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#tab_sub {
    font-size: 12px;
    color: #44445a;
}

QLabel#field_label {
    font-size: 11px;
    font-weight: 600;
    color: #666680;
    letter-spacing: 1px;
}

QLabel#error_label {
    font-size: 12px;
    color: #ff5555;
    padding: 8px 12px;
    background: #1a0a0a;
    border-radius: 6px;
    border: 1px solid #3a1515;
}

QLabel#success_label {
    font-size: 12px;
    color: #55ff99;
    padding: 8px 12px;
    background: #0a1a0f;
    border-radius: 6px;
    border: 1px solid #154a25;
}

QLineEdit {
    background: #0d0d1a;
    border: 1px solid #1e1e35;
    border-radius: 8px;
    color: #ddddee;
    font-size: 13px;
    padding: 10px 14px;
    selection-background-color: #7c4dff;
}

QLineEdit:focus {
    border-color: #7c4dff;
    background: #0f0f20;
}

QLineEdit::placeholder {
    color: #33334a;
}

QPushButton#btn_primary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #7c4dff, stop:1 #5c2ddf);
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 12px;
    letter-spacing: 0.5px;
}

QPushButton#btn_primary:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #9c6dff, stop:1 #7c4dff);
}

QPushButton#btn_primary:pressed {
    background: #5c2ddf;
}

QPushButton#btn_secondary {
    background: transparent;
    color: #7c4dff;
    font-size: 12px;
    font-weight: 600;
    border: 1px solid #2a1a4a;
    border-radius: 8px;
    padding: 10px;
}

QPushButton#btn_secondary:hover {
    background: #1a0a3a;
    border-color: #7c4dff;
}

QPushButton#btn_tab {
    background: transparent;
    color: #44445a;
    font-size: 13px;
    font-weight: 600;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0px;
    padding: 8px 20px;
}

QPushButton#btn_tab_active {
    background: transparent;
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    border: none;
    border-bottom: 2px solid #7c4dff;
    border-radius: 0px;
    padding: 8px 20px;
}

QFrame#divider {
    background: #1a1a2a;
    max-height: 1px;
}
"""


class LoginWindow(QWidget):
    """Ventana de login/registro. Emite login_successful cuando el usuario entra."""

    login_successful = pyqtSignal(object)   # emite el User

    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth = auth_manager
        self.setObjectName("login_root")
        self.setStyleSheet(LOGIN_STYLE)
        self.setMinimumSize(400, 500)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignCenter)

        # Tarjeta central
        card = QWidget()
        card.setObjectName("card")
        card.setFixedWidth(400)
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(124, 77, 255, 80))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 36, 36, 36)
        card_layout.setSpacing(0)

        # Logo
        logo_row = QHBoxLayout()
        logo_row.setSpacing(0)
        logo_row.setAlignment(Qt.AlignCenter)
        logo1 = QLabel("StreamerClips")
        logo1.setObjectName("app_logo")
        logo2 = QLabel("AI")
        logo2.setObjectName("app_logo_ai")
        logo_row.addWidget(logo1)
        logo_row.addWidget(logo2)
        card_layout.addLayout(logo_row)

        tagline = QLabel("CREA · DETECTA · EXPORTA")
        tagline.setObjectName("tagline")
        tagline.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(tagline)
        card_layout.addSpacing(28)

        # Tabs login / registro
        tabs_row = QHBoxLayout()
        tabs_row.setSpacing(0)
        self._btn_tab_login = QPushButton("Iniciar sesión")
        self._btn_tab_login.setObjectName("btn_tab_active")
        self._btn_tab_login.clicked.connect(lambda: self._switch_tab(0))
        self._btn_tab_reg = QPushButton("Crear cuenta")
        self._btn_tab_reg.setObjectName("btn_tab")
        self._btn_tab_reg.clicked.connect(lambda: self._switch_tab(1))
        tabs_row.addWidget(self._btn_tab_login)
        tabs_row.addWidget(self._btn_tab_reg)
        card_layout.addLayout(tabs_row)

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.HLine)
        card_layout.addWidget(div)
        card_layout.addSpacing(24)

        # Stack login / registro
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_login_form())
        self._stack.addWidget(self._build_register_form())
        card_layout.addWidget(self._stack)

        root.addWidget(card, alignment=Qt.AlignCenter)

    # ------------------------------------------------------------------
    # Formulario de login
    # ------------------------------------------------------------------

    def _build_login_form(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        lay.addWidget(self._field_label("EMAIL"))
        self._login_email = QLineEdit()
        self._login_email.setPlaceholderText("tu@email.com")
        lay.addWidget(self._login_email)

        lay.addWidget(self._field_label("CONTRASEÑA"))
        self._login_pwd = QLineEdit()
        self._login_pwd.setPlaceholderText("••••••••")
        self._login_pwd.setEchoMode(QLineEdit.Password)
        self._login_pwd.returnPressed.connect(self._do_login)
        lay.addWidget(self._login_pwd)

        lay.addSpacing(4)

        self._login_msg = QLabel("")
        self._login_msg.setWordWrap(True)
        self._login_msg.hide()
        lay.addWidget(self._login_msg)

        btn = QPushButton("Entrar →")
        btn.setObjectName("btn_primary")
        btn.clicked.connect(self._do_login)
        lay.addWidget(btn)

        lay.addSpacing(8)
        hint = QLabel("¿No tienes cuenta?")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #44445a; font-size: 12px;")
        lay.addWidget(hint)

        btn2 = QPushButton("Crear cuenta gratis")
        btn2.setObjectName("btn_secondary")
        btn2.clicked.connect(lambda: self._switch_tab(1))
        lay.addWidget(btn2)

        return w

    # ------------------------------------------------------------------
    # Formulario de registro
    # ------------------------------------------------------------------

    def _build_register_form(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        lay.addWidget(self._field_label("NOMBRE DE USUARIO"))
        self._reg_user = QLineEdit()
        self._reg_user.setPlaceholderText("TuNombre")
        lay.addWidget(self._reg_user)

        lay.addWidget(self._field_label("EMAIL"))
        self._reg_email = QLineEdit()
        self._reg_email.setPlaceholderText("tu@email.com")
        lay.addWidget(self._reg_email)

        lay.addWidget(self._field_label("CONTRASEÑA"))
        self._reg_pwd = QLineEdit()
        self._reg_pwd.setPlaceholderText("Mínimo 6 caracteres")
        self._reg_pwd.setEchoMode(QLineEdit.Password)
        lay.addWidget(self._reg_pwd)

        lay.addWidget(self._field_label("CONFIRMAR CONTRASEÑA"))
        self._reg_pwd2 = QLineEdit()
        self._reg_pwd2.setPlaceholderText("Repite la contraseña")
        self._reg_pwd2.setEchoMode(QLineEdit.Password)
        self._reg_pwd2.returnPressed.connect(self._do_register)
        lay.addWidget(self._reg_pwd2)

        self._reg_msg = QLabel("")
        self._reg_msg.setWordWrap(True)
        self._reg_msg.hide()
        lay.addWidget(self._reg_msg)

        btn = QPushButton("Crear cuenta →")
        btn.setObjectName("btn_primary")
        btn.clicked.connect(self._do_register)
        lay.addWidget(btn)

        return w

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("field_label")
        return lbl

    def _switch_tab(self, idx: int):
        self._stack.setCurrentIndex(idx)
        if idx == 0:
            self._btn_tab_login.setObjectName("btn_tab_active")
            self._btn_tab_reg.setObjectName("btn_tab")
        else:
            self._btn_tab_login.setObjectName("btn_tab")
            self._btn_tab_reg.setObjectName("btn_tab_active")
        # Refrescar estilos
        self._btn_tab_login.setStyle(self._btn_tab_login.style())
        self._btn_tab_reg.setStyle(self._btn_tab_reg.style())

    def _show_msg(self, label: QLabel, text: str, success: bool = False):
        label.setObjectName("success_label" if success else "error_label")
        label.setStyle(label.style())
        label.setText(text)
        label.show()

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _do_login(self):
        self._login_msg.hide()
        ok, msg = self.auth.login(
            self._login_email.text(),
            self._login_pwd.text()
        )
        if ok:
            self._show_msg(self._login_msg, msg, success=True)
            self.login_successful.emit(self.auth.current_user)
        else:
            self._show_msg(self._login_msg, msg, success=False)

    def _do_register(self):
        self._reg_msg.hide()
        if self._reg_pwd.text() != self._reg_pwd2.text():
            self._show_msg(self._reg_msg, "Las contraseñas no coinciden.")
            return

        ok, msg = self.auth.register(
            self._reg_user.text(),
            self._reg_email.text(),
            self._reg_pwd.text()
        )
        if ok:
            self._show_msg(self._reg_msg, msg + " Ahora inicia sesión.", success=True)
            # Limpiar campos y cambiar a login
            self._reg_user.clear()
            self._reg_email.clear()
            self._reg_pwd.clear()
            self._reg_pwd2.clear()
            self._login_email.setText(self._reg_email.text())
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self._switch_tab(0))
        else:
            self._show_msg(self._reg_msg, msg, success=False)
