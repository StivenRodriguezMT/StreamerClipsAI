"""
core/ffmpeg_handler.py
Wraps FFmpeg for clipping, re-encoding and format conversion.
All operations run in a background QThread so the UI stays responsive.
"""
import os
import subprocess
import shutil
from PyQt5.QtCore import QThread, pyqtSignal


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def find_ffmpeg() -> str:
    """Busca ffmpeg en el PATH y en ubicaciones comunes de Windows."""
    # 1. Buscar en el PATH del sistema
    path = shutil.which("ffmpeg")
    if path:
        return path

    # 2. Forzar recarga del PATH actual (por si se agregó en esta sesión)
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
            sys_path = winreg.QueryValueEx(key, "Path")[0]
        for p in sys_path.split(";"):
            candidate = os.path.join(p.strip(), "ffmpeg.exe")
            if os.path.isfile(candidate):
                return candidate
    except Exception:
        pass

    # 3. Ubicaciones comunes de Windows
    candidates = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        r"C:\Tools\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\ffmpeg.exe",
        os.path.join(os.environ.get("USERPROFILE", ""), r"Downloads\ffmpeg\bin\ffmpeg.exe"),
        os.path.join(os.environ.get("USERPROFILE", ""), r"ffmpeg\bin\ffmpeg.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c

    raise RuntimeError(
        "FFmpeg no encontrado.\n"
        "Por favor instala FFmpeg y agrégalo al PATH de Windows.\n"
        "Descarga: https://ffmpeg.org/download.html"
    )


def seconds_to_hms(seconds: float) -> str:
    """Convert float seconds → HH:MM:SS.mmm string for FFmpeg -ss / -to."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


# -----------------------------------------------------------------------
# Export presets
# -----------------------------------------------------------------------

EXPORT_PRESETS = {
    "TikTok / Shorts (9:16)": {
        "vf": "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "ext": "mp4",
        "extra": ["-c:v", "libx264", "-preset", "fast", "-crf", "23",
                  "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"],
    },
    "YouTube Shorts (9:16)": {
        "vf": "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "ext": "mp4",
        "extra": ["-c:v", "libx264", "-preset", "slow", "-crf", "18",
                  "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart"],
    },
    "Instagram Reels (9:16)": {
        "vf": "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "ext": "mp4",
        "extra": ["-c:v", "libx264", "-preset", "fast", "-crf", "20",
                  "-c:a", "aac", "-b:a", "192k"],
    },
    "Kick Clip (16:9)": {
        "vf": "scale=1280:720",
        "ext": "mp4",
        "extra": ["-c:v", "libx264", "-preset", "fast", "-crf", "23",
                  "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"],
    },
    "Original Quality (16:9)": {
        "vf": None,
        "ext": "mp4",
        "extra": ["-c:v", "libx264", "-preset", "fast", "-crf", "18",
                  "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart"],
    },
    "GIF Preview": {
        "vf": "scale=480:-1:flags=lanczos,fps=15",
        "ext": "gif",
        "extra": [],
    },
}


# -----------------------------------------------------------------------
# Background export thread
# -----------------------------------------------------------------------

class ExportWorker(QThread):
    """
    Runs FFmpeg in a subprocess.  Reports progress via signals.
    """
    progress = pyqtSignal(int)          # 0-100
    finished = pyqtSignal(str)          # output path
    error = pyqtSignal(str)

    def __init__(self, ffmpeg_path, source, start_s, end_s, output_path, preset_name):
        super().__init__()
        self.ffmpeg = ffmpeg_path
        self.source = source
        self.start_s = start_s
        self.end_s = end_s
        self.output_path = output_path
        self.preset_name = preset_name

    def run(self):
        try:
            preset = EXPORT_PRESETS[self.preset_name]
            duration = self.end_s - self.start_s

            cmd = [
                self.ffmpeg, "-y",
                "-ss", seconds_to_hms(self.start_s),
                "-i", self.source,
                "-t", str(duration),
            ]

            if preset["vf"]:
                cmd += ["-vf", preset["vf"]]

            cmd += preset["extra"]
            cmd.append(self.output_path)

            proc = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            # Parse FFmpeg stderr for time= progress
            total = duration
            for line in proc.stderr:
                if "time=" in line:
                    try:
                        t_str = line.split("time=")[1].split(" ")[0]
                        parts = t_str.split(":")
                        elapsed = float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
                        pct = int(min(elapsed / total * 100, 99))
                        self.progress.emit(pct)
                    except Exception:
                        pass

            proc.wait()
            if proc.returncode == 0:
                self.progress.emit(100)
                self.finished.emit(self.output_path)
            else:
                self.error.emit(f"FFmpeg terminó con código {proc.returncode}")

        except Exception as e:
            self.error.emit(str(e))
