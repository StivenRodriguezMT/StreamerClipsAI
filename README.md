# StreamerClipsAI

Aplicación de escritorio para Windows que permite a streamers cargar sus grabaciones, crear clips, detectar highlights automáticamente con IA y exportarlos con subtítulos automáticos para TikTok, YouTube Shorts, Instagram Reels y Kick.

---

## Requisitos

- Python 3.12
- FFmpeg instalado y disponible en el PATH
- VLC Media Player 64-bit

## Instalación

```bash
py -3.12 -m pip install PyQt5 opencv-python numpy openai-whisper python-vlc
py -3.12 -m pip install torch --index-url https://download.pytorch.org/whl/cu128
```

### Instalar FFmpeg en Windows

1. Descarga desde https://ffmpeg.org/download.html
2. Extrae en `C:\ffmpeg\`
3. Agrega `C:\ffmpeg\bin` a la variable de entorno PATH de Windows
4. Verifica: abre una terminal y ejecuta `ffmpeg -version`

### Instalar VLC

Descarga VLC 64-bit desde https://www.videolan.org/vlc/

## Ejecutar

```bash
py -3.12 main.py
```

---

## Funcionalidades

### Autenticación
- Registro e inicio de sesión con email y contraseña
- **Sesión persistente** — no necesitas iniciar sesión cada vez
- Foto de perfil personalizable
- Historial de clips exportados por usuario

### Cargar un video
- Haz clic en **＋ Importar** o presiona `Ctrl+O`
- **Drag & drop** — arrastra un video directo a la ventana
- Recuerda el último video abierto automáticamente
- Formatos soportados: `.mp4`, `.avi`, `.mkv`, `.mov`, `.flv`, `.webm`

### Controles de reproducción
| Tecla | Acción |
|-------|--------|
| `Espacio` | Reproducir / Pausar |
| `←` | Retroceder 10 segundos |
| `→` | Avanzar 10 segundos |
| `Home` | Ir al inicio del video |
| `End` | Ir al final del video |
| `,` | Retroceder 1 frame |
| `.` | Avanzar 1 frame |
| `Ctrl+O` | Abrir video |

### Crear un clip
1. Reproduce el video y encuentra tu momento destacado
2. Presiona **I** para marcar el inicio
3. Presiona **O** para marcar el fin
4. Presiona **P** para previsualizar el clip
5. Asigna un nombre (opcional) y elige el formato
6. Haz clic en **＋ Crear Clip** para guardarlo o **⬆ Exportar** para exportar

### Atajos del editor
| Tecla | Acción |
|-------|--------|
| `I` | Marcar punto de entrada |
| `O` | Marcar punto de salida |
| `P` | Previsualizar clip (IN → OUT) |
| `R` | Resetear IN/OUT |
| `A` | Seleccionar todo el video |
| `L` | Activar/desactivar loop |
| `S` | Captura de pantalla del frame actual |

### Panel Video
- Escala (10% — 300%)
- Posición X / Y
- Rotación (-180° a 180°)

### Panel Audio
- Volumen en dB (-20 a +20)
- Fade in / Fade out

### Panel Velocidad
- Velocidad de exportación (0.1x — 4x)

### Panel Ajustar
- Brillo, Contraste, Saturación, Nitidez
- Temperatura y Tono de color

### Gestión de clips
- Renombrar clips con doble clic
- Duplicar clips
- Ordenar por nombre o duración
- Contador de duración total
- Tamaño estimado del clip

### Exportación
- Al exportar se aplican todos los ajustes (velocidad, color, audio)
- Pregunta si abrir carpeta al terminar
- **Notificación de Windows** al completar
- Carpeta de salida configurable
- Historial de clips exportados

### Formatos de exportación
| Formato | Resolución | Ideal para |
|---------|-----------|------------|
| TikTok / Shorts (9:16) | 1080×1920 | TikTok |
| YouTube Shorts (9:16) | 1080×1920 | YouTube Shorts |
| Instagram Reels (9:16) | 1080×1920 | Instagram |
| Kick Clip (16:9) | 1280×720 | Kick |
| Calidad Original (16:9) | Original | Archivo |
| Vista previa GIF | 480px ancho | Miniaturas |

### Highlights IA
- Detección automática de momentos destacados por picos de audio
- Tarjetas con puntuación y tipo de highlight
- Un clic para agregar como clip

### Subtítulos automáticos
- Integración con Whisper (openai-whisper)
- Modelos: tiny, base, small, medium, large
- Soporte GPU (NVIDIA)

---

## Estructura del proyecto

```
StreamerClipsAI/
├── main.py                          # Punto de entrada
├── requirements.txt
├── core/
│   ├── auth_manager.py              # Autenticación, sesión y historial (SQLite)
│   ├── video_player.py              # Reproducción de video con VLC
│   ├── ffmpeg_handler.py            # Exportación de clips con FFmpeg y presets
│   ├── clip_model.py                # Modelo de datos de un clip
│   ├── highlight_detector.py        # Detección de highlights por audio
│   └── subtitles.py                 # Subtítulos automáticos con Whisper
├── ui/
│   ├── main_window.py               # Editor principal estilo CapCut
│   ├── home_screen.py               # Pantalla de inicio con historial
│   ├── login_window.py              # Login y registro
│   ├── about_dialog.py              # Ventana de créditos y redes sociales
│   ├── profile_widget.py            # Widget de perfil con avatar
│   ├── highlights_panel.py          # Panel de highlights IA
│   ├── history_panel.py             # Historial de clips exportados
│   ├── subtitles_panel.py           # Opciones de subtítulos
│   ├── theme.py                     # Hoja de estilos oscura
│   └── waveform_widget.py           # Timeline / forma de onda
└── video/
    └── video_loader.py              # Carga y metadata de videos
```

---

## Hoja de ruta

- [x] Sesión persistente (no pide login cada vez)
- [x] Drag & drop de videos
- [x] Previsualización de clips (IN → OUT)
- [x] Detección automática de highlights con IA
- [x] Subtítulos automáticos con Whisper
- [x] Ajustes de video (brillo, contraste, saturación, velocidad)
- [x] Notificaciones de Windows al exportar
- [ ] Exportación en lote
- [ ] Subtítulos con faster-whisper (más rápido, sin CUDA DLL issues)
- [ ] Miniaturas reales del video en los clips
- [ ] Importación de chat de Twitch/Kick como marcadores
- [ ] Recorte vertical automático con seguimiento de cara
- [ ] Compartir clip directo a Discord via webhook
