import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # Pre-cargar torch y whisper en el hilo principal para evitar
    # errores de DLL en Windows cuando se usan desde QThread
    try:
        import torch
        import whisper
        _ = torch.zeros(1)  # forzar carga de DLLs ahora
    except Exception:
        pass
    app.setApplicationName("StreamerClipsAI")
    app.setOrganizationName("StreamerClipsAI")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
