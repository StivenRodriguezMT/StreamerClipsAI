DARK_THEME = """
/* ===== StreamerClipsAI — Tema estilo CapCut ===== */

QMainWindow, QWidget {
    background-color: #1a1a1a;
    color: #e8e8e8;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}

/* ══════════════════════════════════════
   TOPBAR
══════════════════════════════════════ */
#topbar {
    background-color: #111111;
    border-bottom: 1px solid #2a2a2a;
    min-height: 48px;
    max-height: 48px;
}

#app_title {
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.5px;
}

#app_subtitle {
    font-size: 10px;
    color: #7c4dff;
    font-weight: 600;
    letter-spacing: 2px;
}

#btn_export_main {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5c2dff, stop:1 #7c4dff);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 700;
}

#btn_export_main:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c4dff, stop:1 #9c6dff);
}

#btn_export_main:disabled {
    background: #2a2a2a;
    color: #555555;
}

/* ══════════════════════════════════════
   PANEL IZQUIERDO (media panel)
══════════════════════════════════════ */
#left_panel {
    background-color: #111111;
    border-right: 1px solid #2a2a2a;
    min-width: 220px;
    max-width: 220px;
}

#left_panel_title {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #555555;
    padding: 14px 16px 8px 16px;
}

#btn_load {
    background-color: #252525;
    color: #cccccc;
    border: 1px dashed #3a3a3a;
    border-radius: 8px;
    padding: 14px;
    font-size: 12px;
    font-weight: 600;
    margin: 8px;
}

#btn_load:hover {
    background-color: #2a2a2a;
    border-color: #7c4dff;
    color: #ffffff;
}

/* Media thumbnail card */
#media_card {
    background-color: #252525;
    border: 1px solid #333333;
    border-radius: 8px;
    margin: 6px 10px;
    padding: 6px;
}

#media_card:hover {
    border-color: #7c4dff;
}

#media_name {
    font-size: 11px;
    color: #aaaaaa;
}

#media_duration {
    font-size: 10px;
    color: #666666;
    font-family: 'Courier New', monospace;
}

/* ══════════════════════════════════════
   ÁREA CENTRAL — VIDEO
══════════════════════════════════════ */
#center_panel {
    background-color: #1a1a1a;
}

#video_container {
    background-color: #0d0d0d;
}

#video_widget {
    background-color: #000000;
}

#overlay_text {
    color: #666666;
    font-size: 18px;
    font-weight: 600;
    line-height: 1.6;
    background: transparent;
    padding: 20px;
}

/* Controles de reproducción centrados */
#playback_controls {
    background-color: #111111;
    border-top: 1px solid #222222;
    min-height: 52px;
    max-height: 52px;
}

#btn_play {
    background-color: #ffffff;
    color: #000000;
    border: none;
    border-radius: 20px;
    min-width: 40px;
    max-width: 40px;
    min-height: 40px;
    max-height: 40px;
    font-size: 14px;
    font-weight: 700;
    padding: 0px;
}

#btn_play:hover {
    background-color: #e0e0e0;
}

#btn_skip {
    background-color: transparent;
    color: #888888;
    border: none;
    font-size: 16px;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    padding: 0px;
    border-radius: 4px;
}

#btn_skip:hover {
    color: #ffffff;
    background-color: #2a2a2a;
}

#timecode_main {
    font-family: 'Courier New', monospace;
    font-size: 13px;
    color: #aaaaaa;
    letter-spacing: 1px;
}

/* ══════════════════════════════════════
   PANEL DERECHO — CLIPS
══════════════════════════════════════ */
#right_panel {
    background-color: #111111;
    border-left: 1px solid #2a2a2a;
    min-width: 200px;
    max-width: 200px;
}

#right_panel_title {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #555555;
    padding: 14px 16px 8px 16px;
}

QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    background-color: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 8px 10px;
    margin: 3px 8px;
    color: #aaaaaa;
}

QListWidget::item:selected {
    background-color: #252535;
    border-color: #7c4dff;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #222222;
    border-color: #3a3a4a;
}

#btn_delete_clip {
    background-color: transparent;
    color: #666666;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 6px;
    font-size: 12px;
    margin: 4px 8px;
}

#btn_delete_clip:hover {
    color: #ff5252;
    border-color: #ff5252;
}

/* ══════════════════════════════════════
   TIMELINE (parte inferior)
══════════════════════════════════════ */
#timeline_panel {
    background-color: #111111;
    border-top: 1px solid #2a2a2a;
    min-height: 180px;
    max-height: 220px;
}

#timeline_toolbar {
    background-color: #0d0d0d;
    border-bottom: 1px solid #222222;
    min-height: 36px;
    max-height: 36px;
    padding: 0px 10px;
}

/* Botones IN / OUT en timeline */
#btn_set_in {
    background-color: transparent;
    color: #00c853;
    border: 1px solid #1a3a25;
    border-radius: 5px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 700;
}

#btn_set_in:hover {
    background-color: #0d2a1a;
    border-color: #00c853;
}

#btn_set_out {
    background-color: transparent;
    color: #ff5252;
    border: 1px solid #3a1a1a;
    border-radius: 5px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 700;
}

#btn_set_out:hover {
    background-color: #2a0d0d;
    border-color: #ff5252;
}

#in_out_display {
    font-family: 'Courier New', monospace;
    font-size: 11px;
    color: #555555;
    padding: 0px 8px;
}

#btn_create_clip {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5c2dff, stop:1 #7c4dff);
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 700;
}

#btn_create_clip:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c4dff, stop:1 #9c6dff);
}

#btn_create_clip:disabled {
    background: #2a2a2a;
    color: #444444;
}

/* Slider del timeline */
#timeline_slider {
    margin: 0px 10px;
}

QSlider#timeline_slider::groove:horizontal {
    height: 3px;
    background: #2a2a2a;
    border-radius: 2px;
}

QSlider#timeline_slider::sub-page:horizontal {
    background: #444444;
    border-radius: 2px;
}

QSlider#timeline_slider::handle:horizontal {
    background: #ffffff;
    width: 2px;
    height: 16px;
    margin: -7px 0;
    border-radius: 1px;
}

/* Volumen */
QSlider#volume_slider::groove:horizontal {
    height: 3px;
    background: #2a2a2a;
    border-radius: 2px;
}

QSlider#volume_slider::sub-page:horizontal {
    background: #666666;
    border-radius: 2px;
}

QSlider#volume_slider::handle:horizontal {
    background: #aaaaaa;
    width: 10px;
    height: 10px;
    margin: -4px 0;
    border-radius: 5px;
}

/* ══════════════════════════════════════
   EXPORT PANEL (popup/inline)
══════════════════════════════════════ */
#export_panel {
    background-color: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 12px;
}

#export_panel_title {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #555555;
}

QComboBox {
    background-color: #222222;
    color: #cccccc;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

QComboBox::drop-down { border: none; width: 20px; }

QComboBox QAbstractItemView {
    background-color: #222222;
    color: #cccccc;
    border: 1px solid #333333;
    selection-background-color: #333344;
}

QLineEdit {
    background-color: #222222;
    color: #cccccc;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

QLineEdit:focus {
    border-color: #7c4dff;
}

QProgressBar {
    background-color: #1a1a1a;
    border: none;
    border-radius: 3px;
    height: 4px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c4dff, stop:1 #00e5ff);
    border-radius: 3px;
}

/* ══════════════════════════════════════
   GENERAL BUTTONS
══════════════════════════════════════ */
QPushButton {
    background-color: #252525;
    color: #aaaaaa;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2e2e2e;
    color: #ffffff;
    border-color: #555555;
}

QPushButton:pressed { background-color: #1a1a1a; }

/* ══════════════════════════════════════
   STATUS BAR
══════════════════════════════════════ */
QStatusBar {
    background-color: #0d0d0d;
    color: #444444;
    font-size: 11px;
    border-top: 1px solid #1e1e1e;
}

/* ══════════════════════════════════════
   SCROLLBAR
══════════════════════════════════════ */
QScrollBar:vertical {
    background: #111111;
    width: 5px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #333333;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #555555; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #111111;
    height: 5px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #333333;
    border-radius: 3px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #555555; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ══════════════════════════════════════
   TOOLTIPS
══════════════════════════════════════ */
QToolTip {
    background-color: #222222;
    color: #dddddd;
    border: 1px solid #333333;
    border-radius: 4px;
    font-size: 12px;
    padding: 4px 8px;
}

QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #222222;
}
"""
