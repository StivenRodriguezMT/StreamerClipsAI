import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget
from PyQt5.QtCore import Qt

from core.auth_manager import AuthManager
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("StreamerClipsAI")
    app.setOrganizationName("StreamerClipsAI")

    # Pre-cargar torch y whisper en el hilo principal
    try:
        import torch
        import whisper
        _ = torch.zeros(1)
    except Exception:
        pass

    # Auth manager compartido
    auth = AuthManager()

    # Ventana apilada: login → app principal
    stack = QStackedWidget()
    stack.setWindowTitle("StreamerClipsAI")
    stack.resize(420, 580)

    login_win = LoginWindow(auth)
    main_win  = MainWindow(auth)

    stack.addWidget(login_win)   # índice 0
    stack.addWidget(main_win)    # índice 1

    def on_login(user):
        """Cuando el usuario entra, cambiar a la ventana principal."""
        main_win.on_user_logged_in(user)
        stack.resize(1380, 820)
        stack.setMinimumSize(1000, 650)
        stack.setCurrentIndex(1)
        stack.setWindowTitle(f"StreamerClipsAI  ·  {user.username}")

    login_win.login_successful.connect(on_login)

    stack.show()
    sys.exit(app.exec_())
