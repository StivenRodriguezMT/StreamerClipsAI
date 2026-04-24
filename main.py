import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget
from PyQt5.QtCore import Qt

from core.auth_manager import AuthManager
from ui.login_window import LoginWindow
from ui.home_screen import HomeScreen
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

    auth = AuthManager()

    # Stack: 0=login, 1=inicio, 2=editor
    stack = QStackedWidget()
    stack.setWindowTitle("StreamerClipsAI")
    stack.resize(420, 580)

    login_win = LoginWindow(auth)
    home_win  = HomeScreen(auth)
    main_win  = MainWindow(auth)

    stack.addWidget(login_win)   # 0
    stack.addWidget(home_win)    # 1
    stack.addWidget(main_win)    # 2

    def on_login(user):
        home_win.set_user(user)
        stack.resize(1100, 700)
        stack.setMinimumSize(800, 600)
        stack.setCurrentIndex(1)
        stack.setWindowTitle(f"StreamerClipsAI  ·  {user.username}")

    def on_open_editor():
        main_win.on_user_logged_in(auth.current_user)
        stack.resize(1380, 820)
        stack.setMinimumSize(1000, 650)
        stack.setCurrentIndex(2)

    def on_logout_from_home():
        auth.logout()
        stack.resize(420, 580)
        stack.setMinimumSize(400, 500)
        stack.setCurrentIndex(0)
        stack.setWindowTitle("StreamerClipsAI")

    def on_logout_from_editor():
        auth.logout()
        stack.resize(420, 580)
        stack.setMinimumSize(400, 500)
        stack.setCurrentIndex(0)
        stack.setWindowTitle("StreamerClipsAI")

    login_win.login_successful.connect(on_login)
    home_win.open_editor.connect(on_open_editor)
    home_win.logout_requested.connect(on_logout_from_home)
    main_win._profile_widget.logout_requested.connect(on_logout_from_editor)

    stack.show()
    sys.exit(app.exec_())
