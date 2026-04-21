"""
core/subtitles.py
Exporta el clip + transcribe con Whisper + quema subtítulos en un solo proceso.
"""
import os
import tempfile
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal

WHISPER_MODELS = {
    "tiny   (más rápido, menos preciso)": "tiny",
    "small  (recomendado — buen balance)": "small",
    "medium (más preciso, más lento)":     "medium",
    "large  (máxima precisión, lento)":    "large",
}

SUBTITLE_STYLE = (
    "FontName=Arial,"
    "FontSize=18,"
    "PrimaryColour=&H00FFFFFF,"
    "OutlineColour=&H00000000,"
    "BackColour=&H80000000,"
    "Bold=1,"
    "Alignment=2,"
    "MarginV=40"
)

def format_srt_time(seconds: float) -> str:
    h  = int(seconds // 3600)
    m  = int((seconds % 3600) // 60)
    s  = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def segments_to_srt(segments) -> str:
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_srt_time(seg["start"])
        end   = format_srt_time(seg["end"])
        text  = seg["text"].strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


class ExportWithSubtitlesWorker(QThread):
    """
    Todo en uno:
      1. Exporta el clip con FFmpeg
      2. Extrae el audio
      3. Transcribe con Whisper
      4. Quema los subtítulos con FFmpeg
      5. Entrega el video final listo
    """
    progress = pyqtSignal(int, str)   # (porcentaje, mensaje)
    finished = pyqtSignal(str)        # ruta del video final
    error    = pyqtSignal(str)

    def __init__(self, ffmpeg_path, source, start_s, end_s,
                 output_path, video_filter, extra_args,
                 model_name="small", use_gpu=False):
        super().__init__()
        self.ffmpeg_path = ffmpeg_path
        self.source      = source
        self.start_s     = start_s
        self.end_s       = end_s
        self.output_path = output_path
        self.video_filter = video_filter
        self.extra_args  = extra_args
        self.model_name  = model_name
        self.use_gpu     = use_gpu

    def run(self):
        tmp_dir     = tempfile.gettempdir()
        tmp_clip    = os.path.join(tmp_dir, "sc_tmp_clip.mp4")
        tmp_wav     = os.path.join(tmp_dir, "sc_tmp_audio.wav")
        tmp_srt     = os.path.join(tmp_dir, "sc_tmp_subs.srt")
        duration    = self.end_s - self.start_s

        try:
            # ── PASO 1: Exportar clip sin subtítulos ──
            self.progress.emit(5, "Exportando clip…")
            cmd = [self.ffmpeg_path, "-y",
                   "-ss", self._hms(self.start_s),
                   "-i", self.source,
                   "-t", str(duration)]
            if self.video_filter:
                cmd += ["-vf", self.video_filter]
            cmd += self.extra_args
            cmd.append(tmp_clip)

            proc = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for line in proc.stderr:
                if "time=" in line:
                    try:
                        t = line.split("time=")[1].split(" ")[0].split(":")
                        elapsed = float(t[0])*3600 + float(t[1])*60 + float(t[2])
                        pct = int(min(elapsed / duration * 30, 30))  # 0-30%
                        self.progress.emit(pct, "Exportando clip…")
                    except Exception:
                        pass
            proc.wait()
            if proc.returncode != 0:
                self.error.emit("Error exportando el clip con FFmpeg.")
                return

            # ── PASO 2: Extraer audio ──
            self.progress.emit(32, "Extrayendo audio…")
            cmd_audio = [
                self.ffmpeg_path, "-y", "-i", tmp_clip,
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                tmp_wav,
            ]
            subprocess.run(
                cmd_audio, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            # ── PASO 3: Transcribir con Whisper ──
            self.progress.emit(38, "Cargando modelo Whisper…")
            try:
                import whisper
                import torch
                device = "cuda" if (self.use_gpu and torch.cuda.is_available()) else "cpu"
            except Exception as e:
                self.error.emit(f"Error cargando Whisper/Torch: {e}\nEjecuta: pip install openai-whisper torch")
                return

            model = whisper.load_model(self.model_name, device=device)
            self.progress.emit(45, "Transcribiendo audio… (puede tardar unos minutos)")

            result = model.transcribe(tmp_wav, language="es", task="transcribe", verbose=False)

            # ── PASO 4: Generar SRT ──
            self.progress.emit(70, "Generando subtítulos…")
            srt_content = segments_to_srt(result["segments"])
            with open(tmp_srt, "w", encoding="utf-8") as f:
                f.write(srt_content)

            # ── PASO 5: Quemar subtítulos ──
            self.progress.emit(75, "Quemando subtítulos en el video…")
            srt_escaped = tmp_srt.replace("\\", "/").replace(":", "\\:")

            cmd_burn = [
                self.ffmpeg_path, "-y", "-i", tmp_clip,
                "-vf", f"subtitles='{srt_escaped}':force_style='{SUBTITLE_STYLE}'",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "copy", "-movflags", "+faststart",
                self.output_path,
            ]
            proc2 = subprocess.Popen(
                cmd_burn, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for line in proc2.stderr:
                if "time=" in line:
                    try:
                        t = line.split("time=")[1].split(" ")[0].split(":")
                        elapsed = float(t[0])*3600 + float(t[1])*60 + float(t[2])
                        pct = 75 + int(min(elapsed / duration * 24, 24))  # 75-99%
                        self.progress.emit(pct, "Quemando subtítulos…")
                    except Exception:
                        pass
            proc2.wait()

            # Limpiar temporales
            for f in [tmp_clip, tmp_wav, tmp_srt]:
                try: os.remove(f)
                except: pass

            if proc2.returncode == 0:
                self.progress.emit(100, "¡Listo!")
                self.finished.emit(self.output_path)
            else:
                self.error.emit("Error quemando subtítulos con FFmpeg.")

        except Exception as e:
            self.error.emit(f"Error: {e}")

    def _hms(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}"
