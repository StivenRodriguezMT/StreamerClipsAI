"""
core/highlight_detector.py
Detecta automáticamente los mejores momentos de un stream
analizando audio + video con IA.

Puntuación final por segundo:
  score = 0.5 * audio_score + 0.3 * motion_score + 0.2 * face_score

Requiere: pip install librosa opencv-python numpy
"""
import os
import cv2
import numpy as np
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List
from PyQt5.QtCore import QThread, pyqtSignal


# -----------------------------------------------------------------------
# Modelo de un highlight detectado
# -----------------------------------------------------------------------

@dataclass
class Highlight:
    start_sec: float      # segundo de inicio
    end_sec:   float      # segundo de fin
    score:     float      # puntuación 0.0 - 1.0
    reason:    str        # motivo: "audio", "movimiento", "reacción", "combinado"

    @property
    def duration(self) -> float:
        return self.end_sec - self.start_sec

    @property
    def score_pct(self) -> int:
        return int(self.score * 100)

    def label(self) -> str:
        icons = {
            "audio":      "🔊",
            "movimiento": "⚡",
            "reacción":   "😮",
            "combinado":  "🔥",
        }
        icon = icons.get(self.reason, "⭐")
        return f"{icon} {self.score_pct}% — {self.reason.capitalize()}"


# -----------------------------------------------------------------------
# Worker principal
# -----------------------------------------------------------------------

class HighlightDetector(QThread):
    """
    Analiza el video completo y emite una lista de highlights detectados.
    """
    progress    = pyqtSignal(int, str)      # (porcentaje, mensaje)
    finished    = pyqtSignal(list)          # lista de Highlight
    error       = pyqtSignal(str)

    # Umbrales configurables
    CLIP_DURATION    = 30.0   # duración de cada clip sugerido (segundos)
    CLIP_PADDING     = 5.0    # segundos antes del pico
    MIN_SCORE        = 0.45   # score mínimo para considerar highlight
    MAX_HIGHLIGHTS   = 10     # máximo de highlights a devolver
    AUDIO_WEIGHT     = 0.50
    MOTION_WEIGHT    = 0.30
    FACE_WEIGHT      = 0.20

    def __init__(self, ffmpeg_path: str, video_path: str):
        super().__init__()
        self.ffmpeg_path = ffmpeg_path
        self.video_path  = video_path

    # ------------------------------------------------------------------
    # Hilo principal
    # ------------------------------------------------------------------

    def run(self):
        try:
            tmp_dir = tempfile.gettempdir()
            tmp_wav = os.path.join(tmp_dir, "sc_detect_audio.wav")

            # ── 1. Extraer audio ──
            self.progress.emit(2, "Extrayendo audio…")
            if not self._extract_audio(tmp_wav):
                self.error.emit("No se pudo extraer el audio del video.")
                return

            # ── 2. Analizar audio ──
            self.progress.emit(10, "Analizando audio…")
            fps_audio, audio_scores = self._analyze_audio(tmp_wav)
            try: os.remove(tmp_wav)
            except: pass

            if audio_scores is None:
                self.error.emit(
                    "No se pudo analizar el audio.\n"
                    "Ejecuta: pip install librosa"
                )
                return

            total_secs = len(audio_scores)

            # ── 3. Analizar video (movimiento + cara) ──
            self.progress.emit(30, "Analizando video… (esto puede tardar)")
            motion_scores, face_scores = self._analyze_video(total_secs)

            # ── 4. Combinar puntuaciones ──
            self.progress.emit(85, "Calculando highlights…")
            final_scores = self._combine_scores(
                audio_scores, motion_scores, face_scores
            )

            # ── 5. Extraer mejores momentos ──
            highlights = self._extract_highlights(final_scores)
            self.progress.emit(100, f"¡Listo! {len(highlights)} highlights encontrados")
            self.finished.emit(highlights)

        except Exception as e:
            self.error.emit(f"Error en detección: {e}")

    # ------------------------------------------------------------------
    # Extracción de audio
    # ------------------------------------------------------------------

    def _extract_audio(self, output_wav: str) -> bool:
        cmd = [
            self.ffmpeg_path, "-y", "-i", self.video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1",
            output_wav,
        ]
        result = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return result.returncode == 0

    # ------------------------------------------------------------------
    # Análisis de audio con librosa
    # ------------------------------------------------------------------

    def _analyze_audio(self, wav_path: str):
        try:
            import librosa
        except ImportError:
            # Fallback: usar numpy directamente con scipy
            try:
                import scipy.io.wavfile as wav
                sr, data = wav.read(wav_path)
                if data.ndim > 1:
                    data = data.mean(axis=1)
                data = data.astype(np.float32)
                # RMS por segundo
                hop = sr
                scores = []
                for i in range(0, len(data) - hop, hop):
                    chunk = data[i:i+hop]
                    rms = np.sqrt(np.mean(chunk**2))
                    scores.append(float(rms))
                scores = np.array(scores)
                scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-8)
                return sr, scores
            except Exception:
                return None, None

        y, sr = librosa.load(wav_path, sr=22050, mono=True)

        # RMS por segundo
        hop_length = sr
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]

        # Onset strength (cambios bruscos de energía)
        onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
        onset = onset[:len(rms)]

        # Combinar RMS + onset
        rms_norm   = (rms   - rms.min())   / (rms.max()   - rms.min()   + 1e-8)
        onset_norm = (onset - onset.min()) / (onset.max() - onset.min() + 1e-8)
        audio_score = 0.6 * rms_norm + 0.4 * onset_norm

        return sr, audio_score.astype(np.float32)

    # ------------------------------------------------------------------
    # Análisis de video (movimiento + detección de cara)
    # ------------------------------------------------------------------

    def _analyze_video(self, total_secs: int):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            return np.zeros(total_secs), np.zeros(total_secs)

        fps        = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        motion_scores = np.zeros(total_secs, dtype=np.float32)
        face_scores   = np.zeros(total_secs, dtype=np.float32)

        # Detector de cara de OpenCV (Haar cascade)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        prev_gray  = None
        frame_idx  = 0
        # Analizar 1 frame cada 0.5 segundos para ser eficiente
        sample_interval = max(1, int(fps * 0.5))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_interval == 0:
                sec = int(frame_idx / fps)
                if sec >= total_secs:
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, (320, 180))

                # ── Movimiento ──
                if prev_gray is not None:
                    diff = cv2.absdiff(prev_gray, gray)
                    motion = float(diff.mean()) / 255.0
                    motion_scores[sec] = max(motion_scores[sec], motion)

                prev_gray = gray

                # ── Cara (muestrear menos frecuente para velocidad) ──
                if frame_idx % (sample_interval * 4) == 0:
                    small = cv2.resize(frame, (320, 180))
                    faces = face_cascade.detectMultiScale(
                        cv2.cvtColor(small, cv2.COLOR_BGR2GRAY),
                        scaleFactor=1.1, minNeighbors=4, minSize=(20, 20)
                    )
                    if len(faces) > 0:
                        # Emoción aproximada: varianza de la región facial
                        for (x, y, w, h) in faces:
                            face_roi = gray[y:y+h, x:x+w]
                            variance = float(face_roi.std()) / 128.0
                            face_scores[sec] = max(face_scores[sec], variance)

                # Reportar progreso cada 500 frames
                if frame_idx % 500 == 0 and total_frames > 0:
                    pct = 30 + int(frame_idx / total_frames * 50)
                    self.progress.emit(pct, f"Analizando video… {int(frame_idx/total_frames*100)}%")

            frame_idx += 1

        cap.release()

        # Normalizar
        def norm(arr):
            mn, mx = arr.min(), arr.max()
            return (arr - mn) / (mx - mn + 1e-8) if mx > mn else arr

        return norm(motion_scores), norm(face_scores)

    # ------------------------------------------------------------------
    # Combinar puntuaciones
    # ------------------------------------------------------------------

    def _combine_scores(self, audio, motion, face) -> np.ndarray:
        n = min(len(audio), len(motion), len(face))
        audio  = audio[:n]
        motion = motion[:n]
        face   = face[:n]

        combined = (
            self.AUDIO_WEIGHT  * audio +
            self.MOTION_WEIGHT * motion +
            self.FACE_WEIGHT   * face
        )

        # Suavizar con ventana deslizante de 3 segundos
        kernel = np.ones(3) / 3
        combined = np.convolve(combined, kernel, mode="same")

        return combined.astype(np.float32)

    # ------------------------------------------------------------------
    # Extraer mejores momentos
    # ------------------------------------------------------------------

    def _extract_highlights(self, scores: np.ndarray) -> List[Highlight]:
        highlights = []
        used_secs  = set()
        total_secs = len(scores)

        # Ordenar segundos por puntuación descendente
        ranked = np.argsort(scores)[::-1]

        for peak_sec in ranked:
            if len(highlights) >= self.MAX_HIGHLIGHTS:
                break
            if scores[peak_sec] < self.MIN_SCORE:
                break

            # Evitar solapamiento
            overlap = any(
                abs(peak_sec - u) < self.CLIP_DURATION
                for u in used_secs
            )
            if overlap:
                continue

            start = max(0.0, peak_sec - self.CLIP_PADDING)
            end   = min(float(total_secs), start + self.CLIP_DURATION)

            # Determinar razón principal
            reason = self._classify_reason(peak_sec, scores)

            highlights.append(Highlight(
                start_sec=start,
                end_sec=end,
                score=float(scores[peak_sec]),
                reason=reason,
            ))
            used_secs.add(peak_sec)

        # Ordenar por tiempo de aparición
        highlights.sort(key=lambda h: h.start_sec)
        return highlights

    def _classify_reason(self, sec: int, scores: np.ndarray) -> str:
        # Clasificación simple basada en la puntuación relativa
        score = scores[sec]
        if score > 0.85:
            return "combinado"
        elif score > 0.70:
            return "reacción"
        elif score > 0.55:
            return "movimiento"
        else:
            return "audio"
