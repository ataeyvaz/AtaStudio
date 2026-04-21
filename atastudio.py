#!/usr/bin/env python3
"""
Ata Studio v5.0 — PyQt6 Edition
MP3→MIDI Dönüştürücü + YouTube/Spotify/SoundCloud İndirici
"""
import os, sys, json, threading, tempfile, shutil, subprocess, re, webbrowser
from pathlib import Path

# ── DNS override — sistem DNS yerine Google/Cloudflare kullan ───────────────
def _patch_dns():
    """Windows sistem DNS'i bazen Python socket'i engelleyebilir.
    socket.getaddrinfo'yu monkey-patch ederek güvenilir DNS'e yönlendir."""
    import socket, urllib.request
    _orig_getaddrinfo = socket.getaddrinfo
    def _patched(host, port, *args, **kwargs):
        try:
            return _orig_getaddrinfo(host, port, *args, **kwargs)
        except socket.gaierror:
            # Sistem DNS başarısız → Google DoH ile dene
            try:
                import urllib.request, json
                url = f"https://dns.google/resolve?name={host}&type=A"
                with urllib.request.urlopen(url, timeout=5) as r:
                    data = json.loads(r.read())
                answers = data.get("Answer", [])
                if answers:
                    ip = answers[0]["data"]
                    return _orig_getaddrinfo(ip, port, *args, **kwargs)
            except Exception:
                pass
            raise  # ikisi de başarısız → orijinal hatayı fırlat
    socket.getaddrinfo = _patched
_patch_dns()

# ── Bağımlılık kontrolü (sadece script modunda, exe'de atla) ────────────────
def _ensure_deps():
    # PyInstaller exe içinde pip çalıştırma — sonsuz döngüye girer!
    # Exe içinde zaten tüm paketler gömülü, kontrol gerekmez.
    if getattr(sys, "frozen", False):
        return  # ← EXE modunda hiç bir şey yapma

    # Sadece .py olarak çalışırken kontrol et
    try:
        import curl_cffi
        ver = tuple(int(x) for x in curl_cffi.__version__.split(".")[:2])
        if not ((ver == (0, 5, 10)) or ((0, 10) <= ver < (0, 15))):
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install",
                 "curl_cffi==0.10.0", "--force-reinstall", "-q"],
                timeout=120)
    except ImportError:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "curl_cffi==0.10.0", "-q"],
                timeout=120)
        except Exception:
            pass
    except Exception:
        pass

_ensure_deps()

from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QUrl, QSize, QTimer)
from PyQt6.QtGui  import (QFont, QColor, QPalette, QIcon)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget,
    QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,
    QSlider, QProgressBar, QScrollArea, QFrame, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QRadioButton, QButtonGroup,
    QSplitter, QTextEdit, QSizePolicy, QSpacerItem,
    QMessageBox, QToolButton,
)

# ── Sabitler ──────────────────────────────────────────────────────────────────
LILYPOND    = r"C:\LilyPond\bin\lilypond.exe"
APP_NAME    = "Ata Studio"
APP_VERSION = "5.0"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".atastudio_config.json")


# ── Kartal görseli (base64 PNG) ─────────────────────────────────────────────
EAGLE_B64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCABGAGgDASIAAhEBAxEB/8QAHAAAAQQDAQAAAAAAAAAAAAAABAADBQcCBggB/8QAORAAAgEDAgQDBQYFBAMAAAAAAQIDAAQRBSEGEjFBBxNRFCJhcYEyQpGhsdEVUnLB8CNDkuFTYqL/xAAaAQACAwEBAAAAAAAAAAAAAAADBAECBQAG/8QAJREAAQQCAQQCAwEAAAAAAAAAAQACAxEEITESE0FRIqEFQnHB/9oADAMBAAIRAxEAPwCz5OL+FrS9a1vdesLWdTgxzyeWc+nvAVlY+JvDNu5ivRe2iZwLgRrPAfj5kLOMfPFVPxwb21V2urPi+xh+7/EtdtuXHwWQMcVVN1fxm/5o2wM/bDI2fjzIig/jR5chwNIccQItdv6Nq2la1b+0aRqVpfxY3a3lD4+YG4+tGblSBXFmkaxbWcyXKXUsU6HmWWGQq/0IOfpmtufxw161hNrazi/tHiaOQXqMXIIIyHB5lO/qelQ3IHkKTD6XUi/ZINNv0Fc4+H/jrqOkpBZ8Q82s2QwvnDa5iH9XSX64Pxq/uGeJ+HuJtM9v0XUFuI1IEiFCskRI6Mp3B/I9jR2StfwhvYW8otxntT1urbe6fwpuWWJm5VZh8loi35Rgcz/hRDwhjlNyoWk5cHJ6DuaCngYHpiqA8cuNdVuNcuNJU3sFvHKHitru0jjlt3XYPHJG/OD1PvdjuKlvCrinxG4v1XSrNrgLpeluG1G8aP3rhcHCO33mI2AHpzGhiWjSuY7Fq3nXB3P5U2epouQAOVyT9KElHKTkt+FNBLlYy9BSpEDbZyKVSoVfar4a6fqk7yWPs+nF+swtFnnY+pklY/kB86r3jbwM4gtYmudKuBrgVS7q3uS5z0Vcnm29CPlV0Q3pUAiUj8KMW/yN55PlkCqyYTXeFEeWWrj+XSb3Srr2fVrM2DrksJ4eVwPgrZb8qem1i0WJlj8tX5cc7DmIz6DoPzrpniXhPhDiJ55tV0wPczqFa6jcpNt094fAY6dKozxI8Jr/AIfaXUuHxLqOmAFsFczQDvzAfaH/ALD6gdaQlw5I9jYT0WXG/R5Wmwrm2ubsS+WyguGLe82PQdPxozwy441nhnXV1azlw6ACZXOUmQn7DjuNuo3GMihNM8iSHmkI2Xox2z/n/VQGqqyTtJAiworEDkTAUdep6nJ6elK3WwmaB0V3FwTxxpXFune16fKIriMAXFrKQJID8fVfRhsfgdqjPE3xHj4ZtTp+nzQzazNHlR1S3U9Hf4+i9+vTryJwnxJqmiavbXumai0ckK5Bx1H8uO4PodjWz6rqF7ruqS381y3tUh57g8gBJPqD02wAOwpo5VsqtpYYxD78KS4U0d+KeLrfSbRyJLmUma4fcqu7PI3rgZPxOK6i0DTdL4b0mPStIkEFtFvgL7zserMe7Huf7VD+B/hXoWi6HacTSapc3F/qNkpkIwscYYhsKCobOwBzWwa3ZpDcOLOSSREco/mxlSD6g9GHxFExnRg/M7KHk9dW0aC8e452ybmQD4LQcsiuTmec/lQ0hn7YGKYdpSd3H1NagjWcXosrE3+/L9WpVFyFs7yDJ6YNKr9s+1TuD0sLdgmMxAnbbloxJGZhmFMH1AqHXUBjAV9+u+1EpqChcBCPqaKY3HwhNkb7UpCXDnkQKR35RTnPdE9t/TFRkeoBgf8ATDfHJr323JIWJQO+Kr2z6Vu4Paqjxb8Np/bm4g4dtQyHL3dlFhSCB9tFHr3AGR261U11pGpaoee20i6lhHOz4hIiXkGWJPQY7j4V1d7WWYBVBPr1prUFS9sJ7C6SM21whjkV3CAhtupIpGb8e0kuuk5DnuaOmrXKvEVgkZtBbOkZFv8A6jADmc8223yz9BRFkXNu0kSqBH1Hc99/WrC8S/CnWdBgS6luLaSBoPMaWEO4jHNgK5x7oxvnYbGq7tZPZG9nklj58ZHlnYg+n7fCsUijS2WmxasnwY8RuLtS1i24Kt9aW20srJnzlDypEoyVjPUN6dh17VesLRQI0dvNKkbLykczEEem/WuTeGbbT7LiFJI7r+GQl1mN2VZ/JYemPjkhe5O+1XlpnEEWsw6hc6dGlwWRIo5ZeZedApDuyKS32skIvY9fU8M0TQY3sLjzxfH+pSeKQnra4Af2lvZ9nKkq5YZwd+lDSSQDqP0qNtQ0dsq7uSM55AoG3YDp8q8lkI+6B9a9FGwloLtFYj3gEgbRpntj1wMeoFKol5iDuBj+qlRO2h91BwTq/Tm/5gU6l5HzeXzgEdub/qtei023yWZZGXHeJlz9SRR0OnWrYZbSFgOhxk/of1o5AQhamGvoQy4Kn5Of2rJ9ShTfMGf6mP8AaoiOxWR8fw+2QD+ZB736VnLpCMhPs9tCdt1Tp+Oaim+VNuQPFEEmqzRSWuuexKq8rqjPgj8QM03oehWthdw31trV3LdxH3J5CHIJ64B2H+b9qlLbRhDCWZrZierGNRTa6BYNK0ty6N3XD7fPbFLvxMd5LnC0ZmTO0AA0sOJNLOuW19BqGq38kV2gDBpSFXpk4BAJ22JBwM1A6fwTwZFpy6fFBDJIrh3nYs0ztkdSO22MVss2i6bMiR3VwWVeiM7HH6U5BpukJB5aQhQfvBSM/XFcMXHHDfpcZ5j+32hLjQeGRHNDNZWSQXEiSvAUZUZ1BCty9MjJ+FGRX1hZRiKCa3RF/lQ7V6NM0yFiyRWpyOvlgsP8+JpCHS40zGtzNKf/ABRDI+oJojWxt4H0qOc88lNtxBY7gXsTE9Nm/TFNPrVtn7Zb1Kwv+1FC2SJPOuPOgXstzPy5PyG9B3E9u/uxctwO4XYH6miCvCGb8rCXV0DbQyMPXyz+9Kskt4t3W2eEkfccZH70qmwF3TaZt5g5BRSHI6sc0dbu7y+VyoXx9roKVKqlWCynlFvkyYONzyqP70CeILMXIVIps/FF/elSqWi1B0vdav8A2SNZjCACvNlG94g9j07VrkPGtt56wNBclefAAC4x2GKVKlp9O0mYdt2tgS11HUdOe606RIl6jzJirKMZIGFNRhi1OC0jvbi8EcEhKqis8jD5nKUqVIxvcTspp7GgaCBvdeTTZhHzu5IyrC3HN/yZ2qR0riBdQtmkSKbCqGYyTPk5OMbMBSpVLZHdyrXGNvRdJ9NStkRZmsYgx6MAWP8A9E1mt8ZsOLiWP0CwoAKVKteL5RglZko6XkBGwW8tygIlhYduaAKfyNKlSqhJBUgL/9k="
DEFAULT_BASE = os.path.join(os.path.expanduser("~"), "Documents", "Ata Studio")
DEFAULT_DIRS = {
    "mp3":  os.path.join(DEFAULT_BASE, "mp3"),
    "wav":  os.path.join(DEFAULT_BASE, "wav"),
    "mp4":  os.path.join(DEFAULT_BASE, "mp4"),
    "midi": os.path.join(DEFAULT_BASE, "midi"),
    "pdf":  os.path.join(DEFAULT_BASE, "pdf"),
    "xml":  os.path.join(DEFAULT_BASE, "xml"),
}

CHANNELS = [
    {"name": "Melody",      "program": 73,  "min": 65, "max": 127},
    {"name": "Harmony Hi",  "program": 48,  "min": 52, "max": 64},
    {"name": "Harmony Mid", "program": 25,  "min": 40, "max": 51},
    {"name": "Bass",        "program": 32,  "min": 28, "max": 39},
    {"name": "Sub Bass",    "program": 43,  "min": 0,  "max": 27},
]

# Renk paleti
NAV  = "#0A0A0A"
GOLD = "#FFFFFF"
GOLD2= "#CCCCCC"
BG   = "#F7F7F7"
BG2  = "#EEEEEE"
PNL  = "#FFFFFF"
TXT  = "#111111"
TMID = "#444444"
TLT  = "#888888"
SUCC = "#2E7D32"
ERR  = "#C62828"
BORD = "#DDDDDD"

# ── Stil sayfası ──────────────────────────────────────────────────────────────
APP_STYLE = f"""
QMainWindow, QDialog {{
    background: {BG};
}}
QWidget {{
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    color: {TXT};
}}
/* --- Genel buton --- */
QPushButton {{
    background: {PNL};
    color: {TXT};
    border: 1px solid {BORD};
    border-radius: 4px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    background: {BG2};
}}
QPushButton:disabled {{
    color: #aaa;
}}
/* --- Gold buton (siyah/beyaz tema) --- */
QPushButton[role="gold"] {{
    background: #1A1A1A;
    color: white;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 7px 18px;
    font-weight: bold;
}}
QPushButton[role="gold"]:hover {{
    background: #333333;
}}
QPushButton[role="gold"]:disabled {{
    background: #666666;
    color: #999;
}}
/* --- Kırmızı buton --- */
QPushButton[role="red"] {{
    background: {ERR};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
}}
QPushButton[role="red"]:hover {{
    background: #E74C3C;
}}
/* --- Navy buton --- */
QPushButton[role="navy"] {{
    background: {NAV};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
}}
QPushButton[role="navy"]:hover {{
    background: #222222;
}}
/* --- Platform butonları --- */
QPushButton[role="platform"] {{
    background: {BG2};
    color: {TMID};
    border: 1px solid {BORD};
    border-radius: 4px;
    padding: 5px 10px;
    font-size: 9pt;
}}
QPushButton[role="platform"]:hover {{
    background: #1A1A1A;
    color: white;
    border-color: #1A1A1A;
}}
/* --- Tab butonları --- */
QPushButton[role="tab"] {{
    background: transparent;
    color: {TMID};
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0;
    padding: 10px 22px;
    font-weight: bold;
}}
QPushButton[role="tab"]:checked {{
    color: {NAV};
    border-bottom: 2px solid #FFFFFF;
    background: {PNL};
}}
QPushButton[role="tab"]:hover {{
    background: {BG};
}}
/* --- Giriş alanları --- */
QLineEdit, QComboBox {{
    background: {PNL};
    border: 1px solid {BORD};
    border-radius: 4px;
    padding: 5px 8px;
    color: {TXT};
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {GOLD};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
/* --- Tablo --- */
QTableWidget {{
    background: {PNL};
    gridline-color: {BORD};
    border: 1px solid {BORD};
    border-radius: 4px;
    selection-background-color: #D4AE6330;
}}
QTableWidget::item {{
    padding: 4px;
}}
QHeaderView::section {{
    background: {BG2};
    color: {TMID};
    border: none;
    border-right: 1px solid {BORD};
    border-bottom: 1px solid {BORD};
    padding: 6px 8px;
    font-weight: bold;
}}
/* --- Kaydırma çubuğu --- */
QScrollBar:vertical {{
    background: {BG2};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORD};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
/* --- Progress bar --- */
QProgressBar {{
    background: {BG2};
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    font-size: 8pt;
    color: {TXT};
}}
QProgressBar::chunk {{
    background: {GOLD};
    border-radius: 3px;
}}
/* --- Panel çerçeve --- */
QFrame[role="panel"] {{
    background: {PNL};
    border: 1px solid {BORD};
    border-radius: 6px;
}}
QFrame[role="section"] {{
    background: {BG2};
    border-radius: 4px;
}}
/* --- Text alanı --- */
QTextEdit {{
    background: {BG2};
    border: 1px solid {BORD};
    border-radius: 4px;
    color: {TXT};
    font-family: "Courier New", monospace;
    font-size: 9pt;
}}
/* --- Onay kutusu --- */
QCheckBox {{
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {BORD};
    border-radius: 3px;
    background: {PNL};
}}
QCheckBox::indicator:checked {{
    background: {GOLD};
    border-color: {GOLD};
}}
"""

# ── Yapılandırma ──────────────────────────────────────────────────────────────
def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Config kayıt hatası: {e}")

def create_dirs(base):
    dirs = {
        "mp3":  os.path.join(base, "mp3"),
        "wav":  os.path.join(base, "wav"),
        "mp4":  os.path.join(base, "mp4"),
        "midi": os.path.join(base, "midi"),
        "pdf":  os.path.join(base, "pdf"),
        "xml":  os.path.join(base, "xml"),
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    return dirs

# ── İş motoru fonksiyonları ───────────────────────────────────────────────────
def _sanitize(name):
    """Windows için geçersiz karakterleri temizle (⧸ dahil)."""
    return re.sub(r'[<>:"/\\|?*\u29f8\u29f9]', '_', name).strip('. ')


# Stem → GM enstrüman haritası
# vocals=54(SynthVoice), bass=33(ElecBass), other=25(Guitar), drums=Ch10
# Stem → GM enstrüman haritası
STEM_MAP = {
    "vocals": {"program": 54, "name": "Vocals", "is_drum": False},
    "bass":   {"program": 33, "name": "Bass",   "is_drum": False},
    "other":  {"program": 25, "name": "Other",  "is_drum": False},
    "drums":  {"program": 0,  "name": "Drums",  "is_drum": True },
}


def _find_separator_exe():
    """audio-separator yürütülebilir dosyasını bul."""
    # Venv Scripts klasörü
    scripts = os.path.join(os.path.dirname(sys.executable), "audio-separator.exe")
    if os.path.exists(scripts):
        return scripts
    scripts2 = os.path.join(os.path.dirname(sys.executable), "audio-separator")
    if os.path.exists(scripts2):
        return scripts2
    # PATH'te ara
    found = shutil.which("audio-separator")
    if found:
        return found
    raise RuntimeError(
        "audio-separator komutu bulunamadı.\n"
        "Lütfen çalıştırın: pip install audio-separator")


def _run_separator(input_path, tmp_dir, log_cb):
    """
    audio-separator CLI ile Vocals + Instrumental ayır.
    Subprocess olarak çalışır → numpy/TF çakışması olmaz.
    CPU'da ~1-3 dk, profesyonel kalite.
    """
    exe     = _find_separator_exe()
    out_dir = os.path.join(tmp_dir, "separated")
    os.makedirs(out_dir, exist_ok=True)

    # Unicode path güvenliği — ASCII-safe isimle kopyala
    safe_path = os.path.join(tmp_dir, "ata_track.wav")
    shutil.copy2(input_path, safe_path)

    # Model: Kim Jeong-yeop Roformer — Vocals/Instrumental, CPU'da hızlı
    model = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"

    cmd = [
        exe,
        "--model_filename", model,
        "--output_dir",     out_dir,
        "--output_format",  "WAV",
        "--log_level",      "warning",
        safe_path,
    ]

    log_cb("  🎛️  audio-separator başlatılıyor...")
    log_cb("  ⏳  İlk çalışmada model indiriliyor (~450MB), bir kez indirilir...")

    result = subprocess.run(
        cmd,
        capture_output=True,
        timeout=600,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"audio-separator hatası:\n{result.stderr[-500:]}")

    # Çıktı dosyalarını bul ve eşleştir
    out_files = [
        os.path.join(out_dir, f)
        for f in os.listdir(out_dir)
        if f.lower().endswith(".wav")
    ]

    stems = {}
    for f in out_files:
        fname = os.path.basename(f).lower()
        if "vocal" in fname:
            stems["vocals"] = f
            log_cb("  ✅ Vocals ayrıştırıldı")
        elif any(k in fname for k in ("instrumental","no_vocal","instrum","other")):
            stems["other"] = f
            log_cb("  ✅ Instrumental ayrıştırıldı")

    # Fallback: ilk 2 dosyayı vocal/other olarak ata
    if not stems and len(out_files) >= 2:
        out_files.sort()
        stems["vocals"] = out_files[0]
        stems["other"]  = out_files[1]
        log_cb(f"  ✅ {len(out_files)} dosya bulundu, atandı")
    elif not stems and len(out_files) == 1:
        stems["other"] = out_files[0]
        log_cb("  ✅ 1 stem bulundu")

    if not stems:
        raise RuntimeError(
            "audio-separator çıktı dosyaları bulunamadı.\n"
            f"Çıktı klasörü: {out_dir}")

    log_cb(f"  🎉 Tamamlandı → {len(stems)} stem")
    return stems


def _predict_stem(wav_path, onset, log_cb, stem_name):
    """Basic Pitch ile tek stem → nota listesi."""
    from basic_pitch.inference import predict
    log_cb(f"  🎵 Basic Pitch → {stem_name}...")
    _, midi_data, _ = predict(
        wav_path,
        onset_threshold=float(onset),
        frame_threshold=0.3,
        minimum_note_length=58,
        minimum_frequency=32.7,
        maximum_frequency=2093.0,
        melodia_trick=True,
        multiple_pitch_bends=False,
    )
    notes = [n for inst in midi_data.instruments for n in inst.notes]
    log_cb(f"     → {len(notes)} nota")
    return notes


def convert_file(input_path, out_dirs, bpm, onset, make_xml, make_pdf,
                 progress_cb, log_cb):
    import pretty_midi

    base     = _sanitize(os.path.splitext(os.path.basename(input_path))[0])
    mid_path = os.path.join(out_dirs["midi"], base + ".mid")
    xml_path = os.path.join(out_dirs["xml"],  base + ".musicxml")
    pdf_path = (os.path.join(out_dirs["pdf"], base + ".pdf")
                if make_pdf else None)

    log_cb(f"▶ {os.path.basename(input_path)} işleniyor...")
    progress_cb(3, "Hazırlanıyor...")

    with tempfile.TemporaryDirectory() as tmp:

        # ── 1. audio-separator stem ayrıştırma ──────────────────────────────
        progress_cb(8, "audio-separator: ses katmanları ayrıştırılıyor...")
        try:
            stems = _run_separator(input_path, tmp, log_cb)
        except Exception as e:
            log_cb(f"  ❌ audio-separator başarısız: {e}")
            log_cb("  ⚠ Fallback: tek kanal moduna geçiliyor...")
            stems = None

        new_midi    = pretty_midi.PrettyMIDI(initial_tempo=float(bpm))
        inst_count  = 0
        total_notes = 0

        if stems:
            # ── 2a. Her stem için Basic Pitch ──────────────────────────────
            stem_list  = [s for s in ("vocals","bass","other","drums") if s in stems]
            n_stems    = len(stem_list)

            for i, stem_name in enumerate(stem_list):
                pct_start = 25 + int(i * 40 / n_stems)
                pct_end   = 25 + int((i+1) * 40 / n_stems)
                progress_cb(pct_start, f"Basic Pitch → {stem_name}...")

                wav_path = stems[stem_name]
                info     = STEM_MAP[stem_name]

                if stem_name == "drums":
                    # Davul: Basic Pitch pitch tespiti yetersiz —
                    # ham sesi percussion kanalına boş track olarak ekle
                    drum_inst = pretty_midi.Instrument(
                        program=0, is_drum=True, name="Drums")
                    try:
                        notes = _predict_stem(wav_path, onset, log_cb, "drums")
                        # Davul notalarını Ch10 için pitch=36 (Kick) bazlı yerleştir
                        for n in notes:
                            kick = pretty_midi.Note(
                                velocity=max(60, min(120, n.velocity)),
                                pitch=36, start=n.start, end=n.end)
                            drum_inst.notes.append(kick)
                        inst_count  += 1
                        total_notes += len(drum_inst.notes)
                        log_cb(f"  🥁 Drums → {len(drum_inst.notes)} vuruş")
                    except Exception as e:
                        log_cb(f"  ⚠ Drums Basic Pitch hatası: {e}")
                    new_midi.instruments.append(drum_inst)
                else:
                    try:
                        notes = _predict_stem(wav_path, onset, log_cb, stem_name)
                        if notes:
                            inst = pretty_midi.Instrument(
                                program=info["program"],
                                is_drum=False,
                                name=info["name"])
                            inst.notes  = sorted(notes, key=lambda n: n.start)
                            new_midi.instruments.append(inst)
                            inst_count  += 1
                            total_notes += len(notes)
                            log_cb(f"  🎵 {stem_name:8s} (GM:{info['program']:3d})"
                                   f" → {len(notes):4d} nota")
                    except Exception as e:
                        log_cb(f"  ⚠ {stem_name} Basic Pitch hatası: {e}")

                progress_cb(pct_end, f"{stem_name} tamamlandı")

        else:
            # ── 2b. Fallback: eski tek-kanal mod ──────────────────────────
            progress_cb(25, "Basic Pitch analizi (fallback)...")
            from basic_pitch.inference import predict
            _, midi_data, _ = predict(
                input_path,
                onset_threshold=float(onset),
                frame_threshold=0.3,
                minimum_note_length=58,
                minimum_frequency=32.7,
                maximum_frequency=2093.0,
                melodia_trick=True,
                multiple_pitch_bends=False,
            )
            all_notes = [n for inst in midi_data.instruments for n in inst.notes]
            log_cb(f"  Ham nota (fallback): {len(all_notes)}")
            for ch in CHANNELS:
                notes = sorted(
                    [n for n in all_notes if ch["min"] <= n.pitch <= ch["max"]],
                    key=lambda n: n.start)
                if not notes:
                    continue
                inst = pretty_midi.Instrument(
                    program=ch["program"], is_drum=False, name=ch["name"])
                inst.notes   = notes
                new_midi.instruments.append(inst)
                inst_count  += 1
                total_notes += len(notes)
                log_cb(f"  🎵 {ch['name']:12s} → {len(notes):4d} nota")
            progress_cb(65, "Fallback tamamlandı")

        # ── 3. MIDI kaydet ─────────────────────────────────────────────────
        progress_cb(70, "MIDI kaydediliyor...")
        new_midi.write(mid_path)
        log_cb(f"  ✅ MIDI: {os.path.basename(mid_path)}")

        # ── 4. MusicXML ────────────────────────────────────────────────────
        progress_cb(75, "MusicXML oluşturuluyor...")
        if not make_xml:
            xml_path = None
        else:
            try:
                from music21 import (stream, note as m21note,
                                      duration as m21dur,
                                      instrument as m21inst,
                                      tempo as m21tempo, metadata)
                m21_map = {
                    54: m21inst.Vocalist,
                    33: m21inst.ElectricBass,
                    25: m21inst.AcousticGuitar,
                    0:  m21inst.Percussion,
                }
                score = stream.Score()
                score.metadata = metadata.Metadata()
                score.metadata.title    = base
                score.metadata.composer = APP_NAME
                for i, inst in enumerate(new_midi.instruments):
                    if inst.is_drum:
                        continue          # Perküsyon XML'e zor giriyor, atla
                    part = stream.Part()
                    part.id = inst.name
                    part.append(m21_map.get(inst.program, m21inst.Piano)())
                    if i == 0:
                        part.append(m21tempo.MetronomeMark(number=bpm))
                    for note in inst.notes:
                        n = m21note.Note()
                        n.pitch.midi = note.pitch
                        ql = round(float(note.end - note.start) * (bpm/60) * 4) / 4
                        ql = max(0.25, ql)
                        n.duration = m21dur.Duration(quarterLength=ql)
                        n.offset   = round(float(note.start) * (bpm/60) * 4) / 4
                        part.append(n)
                    score.append(part)
                score.write("musicxml", fp=xml_path)
                log_cb(f"  ✅ MusicXML: {os.path.basename(xml_path)}")
            except Exception as e:
                import traceback; traceback.print_exc()
                log_cb(f"  ⚠ MusicXML hatası: {e}")
                xml_path = None

        # ── 5. PDF ────────────────────────────────────────────────────────
        if make_pdf:
            progress_cb(88, "PDF hazırlanıyor...")
            try:
                import music21
                from music21 import converter
                with tempfile.TemporaryDirectory() as tmp2:
                    ly_path  = os.path.join(tmp2, "score.ly")
                    out_base = os.path.join(tmp2, "score")
                    score2   = converter.parse(mid_path)
                    if not score2.parts or not any(
                            p.flatten().notes for p in score2.parts):
                        raise ValueError("Boş score — PDF atlandı")
                    lp = music21.lily.translate.LilypondConverter()
                    lp.loadObjectFromScore(score2, makeNotation=True)
                    ly_str = str(lp.topLevelObject)
                    with open(ly_path, "w", encoding="utf-8") as f:
                        f.write(ly_str)
                    result = subprocess.run(
                        [LILYPOND, "--pdf", f"-o{out_base}", ly_path],
                        capture_output=True, text=True, timeout=180)
                    tmp_pdf = out_base + ".pdf"
                    if os.path.exists(tmp_pdf):
                        shutil.copy(tmp_pdf, pdf_path)
                        log_cb(f"  ✅ PDF: {os.path.basename(pdf_path)}")
                    else:
                        raise RuntimeError(
                            result.stderr[:300] if result.stderr
                            else "PDF oluşturulamadı")
            except Exception as e:
                import traceback; traceback.print_exc()
                log_cb(f"  ⚠ PDF hatası: {e}")
                pdf_path = None

    progress_cb(100, f"✓ {inst_count} stem · {total_notes} nota")
    return mid_path, xml_path, pdf_path, inst_count, total_notes


def _spotify_search_query(url):
    try:
        with tempfile.TemporaryDirectory() as tmp:
            save_path = os.path.join(tmp, "meta.spotdl")
            r = subprocess.run(
                ["spotdl", "save", url, "--save-file", save_path],
                capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and os.path.exists(save_path):
                with open(save_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                songs = data if isinstance(data, list) else data.get("songs", [])
                if songs:
                    s = songs[0]
                    name   = s.get("name", "")
                    artist = s.get("artist",
                                   s.get("artists", [""])[0]
                                   if isinstance(s.get("artists"), list) else "")
                    if name:
                        return f"{artist} {name}".strip()
    except Exception:
        pass
    return None


def download_url(url, out_dirs, fmt, quality, progress_cb, log_cb):
    import yt_dlp
    url = url.strip()
    if not url:
        raise ValueError("URL boş!")

    is_spotify    = "spotify.com" in url
    is_youtube    = "youtube.com" in url or "youtu.be" in url
    is_soundcloud = "soundcloud.com" in url
    is_plain_text = not (is_spotify or is_youtube or is_soundcloud
                         or url.startswith("http"))

    if is_spotify:
        log_cb("  🎵 Spotify linki algılandı, metadata alınıyor...")
        progress_cb(8, "Spotify metadata...")
        search_query = _spotify_search_query(url)
        if not search_query:
            slug = url.rstrip("/").split("/")[-1].split("?")[0]
            search_query = re.sub(r"[_-]", " ", slug)
            log_cb(f"  ⚠ Metadata alınamadı, URL slug: {search_query}")
        else:
            log_cb(f"  ✅ Sorgu: {search_query}")
        progress_cb(15, f"YouTube'da aranıyor: {search_query[:40]}...")
        ytdl_url = f"ytsearch1:{search_query}"
        platform = "Spotify→YouTube"

    elif is_plain_text:
        search_query = url.strip()
        log_cb(f"  🔍 Metin araması: {search_query}")
        progress_cb(5, f"YouTube'da aranıyor: {search_query[:40]}...")
        ytdl_url = f"ytsearch1:{search_query}"
        platform = "Metin→YouTube"

    else:
        ytdl_url = url
        # Platform ismini URL'den çıkar (label amaçlı)
        _known = [
            ("youtube", "YouTube"), ("youtu.be", "YouTube"),
            ("spotify", "Spotify"), ("soundcloud", "SoundCloud"),
            ("tiktok", "TikTok"), ("instagram", "Instagram"),
            ("twitter", "Twitter"), ("x.com", "X"),
            ("facebook", "Facebook"), ("vimeo", "Vimeo"),
            ("dailymotion", "Dailymotion"), ("twitch", "Twitch"),
            ("bilibili", "Bilibili"), ("rumble", "Rumble"),
            ("xhamster", "XHamster"), ("pornhub", "PornHub"),
            ("xvideos", "XVideos"), ("xnxx", "XNXX"),
            ("redtube", "RedTube"), ("youporn", "YouPorn"),
        ]
        platform = next((name for key, name in _known if key in url.lower()),
                        url.split("/")[2] if url.startswith("http") else "Bilinmeyen")
        log_cb(f"  📥 {platform}: {url[:60]}...")
        progress_cb(5, f"{platform} bilgisi alınıyor...")

    out_dir = out_dirs.get(fmt, out_dirs.get("mp3", ""))

    def hook(d):
        if d["status"] == "downloading":
            try:
                pct = float(
                    d.get("_percent_str", "0%").strip().replace("%", ""))
                progress_cb(15 + int(pct * 0.8), f"İndiriliyor {pct:.0f}%")
            except Exception:
                pass
        elif d["status"] == "finished":
            progress_cb(95, "Dönüştürülüyor...")

    # Sistemde hangi tarayıcı var → impersonation için kullan
    def _find_impersonate_target():
        import shutil
        for browser in ("chrome", "chrome-browser", "chromium", "chromium-browser",
                        "google-chrome", "firefox", "firefox-bin", "msedge", "edge",
                        "safari", "opera", "brave", "vivaldi"):
            if shutil.which(browser):
                # yt-dlp impersonate string formatı
                if "chrom" in browser:   return "chrome"
                if "firefox" in browser: return "firefox"
                if "edge" in browser:    return "edge"
                if "safari" in browser:  return "safari"
        return None

    _impersonate_target = _find_impersonate_target()

    # Proxy ayarı — config'den veya env'den al
    _proxy = (
        load_config().get("proxy", "")          # settings'ten
        or os.environ.get("YTDLP_PROXY", "")     # env değişkeninden
    )

    _common = {
        "progress_hooks":        [hook],
        "quiet":                 True,
        "noplaylist":            True,
        "sleep_interval":        2,
        "max_sleep_interval":    5,
        "nocheckcertificate":    True,   # SSL sertifika hataları için
        "legacy_server_connect": True,   # WRONG_VERSION_NUMBER / eski TLS için
    }
    if _proxy:
        _common["proxy"] = _proxy
    # HLS/DASH skip → sadece YouTube'a özel (diğer 1740+ platform etkilenmesin)
    if is_youtube:
        _common["extractor_args"] = {"youtube": {"skip": ["dash", "hls"]}}
    # İmpersonation → tarayıcı taklit (Dailymotion, porno siteleri vs. için gerekli)
    if _impersonate_target and not is_youtube and not is_spotify:
        _common["impersonate"] = _impersonate_target

    if fmt in ("mp3", "wav"):
        opts = {
            "format":         "bestaudio/best",
            "outtmpl":        os.path.join(out_dir, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key":              "FFmpegExtractAudio",
                "preferredcodec":   fmt,
                "preferredquality": "0",
            }],
            **_common,
        }
    else:
        opts = {
            "format":              "bestvideo+bestaudio/best",
            "outtmpl":             os.path.join(out_dir, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            **_common,
        }

    def _run_download(download_opts):
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            info = ydl.extract_info(ytdl_url, download=True)
            if info and "entries" in info:
                info = info["entries"][0] if info["entries"] else info
            return info

    # 1. Deneme: impersonation ile (varsa)
    try:
        info = _run_download(opts)
    except Exception as e:
        err_str = str(e)
        # impersonation hatası → temiz opts ile tekrar dene
        if "impersonat" in err_str.lower() or "curl_cffi" in err_str.lower():
            log_cb("  ⚠ İmpersonation başarısız, direkt bağlantı deneniyor...")
            opts_clean = {k: v for k, v in opts.items() if k != "impersonate"}
            info = _run_download(opts_clean)
        else:
            raise

    title = info.get("title", "?") if info else "?"
    log_cb(f"  ✅ [{platform}] {title}")
    progress_cb(100, "✓ Tamamlandı!")


# ── QThread İşçileri ──────────────────────────────────────────────────────────
class ConvertWorker(QThread):
    progress = pyqtSignal(int, str)
    log      = pyqtSignal(str)
    done     = pyqtSignal(str, str, str, int, int)  # mid, xml, pdf, ic, tn
    error    = pyqtSignal(str)

    def __init__(self, input_path, out_dirs, bpm, onset, make_xml, make_pdf):
        super().__init__()
        self.input_path = input_path
        self.out_dirs   = out_dirs
        self.bpm        = bpm
        self.onset      = onset
        self.make_xml   = make_xml
        self.make_pdf   = make_pdf

    def run(self):
        try:
            mid, xml, pdf, ic, tn = convert_file(
                self.input_path, self.out_dirs,
                self.bpm, self.onset, self.make_xml, self.make_pdf,
                lambda p, s: self.progress.emit(p, s),
                lambda m: (self.log.emit(m), print(m)),
            )
            print(f"[ConvertWorker] done → mid={mid!r} xml={xml!r} pdf={pdf!r} ic={ic} tn={tn}")
            self.done.emit(mid or "", xml or "", pdf or "", ic, tn)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))


class DownloadWorker(QThread):
    progress = pyqtSignal(int, str)
    log      = pyqtSignal(str)
    done     = pyqtSignal()
    error    = pyqtSignal(str)

    def __init__(self, url, out_dirs, fmt, quality):
        super().__init__()
        self.url      = url
        self.out_dirs = out_dirs
        self.fmt      = fmt
        self.quality  = quality

    def run(self):
        try:
            download_url(
                self.url, self.out_dirs, self.fmt, self.quality,
                lambda p, s: self.progress.emit(p, s),
                lambda m: self.log.emit(m),
            )
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))


# ── Yardımcı widget'lar ───────────────────────────────────────────────────────
def _label(text, bold=False, size=10, color=TXT, parent=None):
    lbl = QLabel(text, parent)
    f = QFont("Helvetica Neue", size)
    f.setBold(bold)
    lbl.setFont(f)
    lbl.setStyleSheet(f"color: {color};")
    return lbl


def _btn(text, role="default", parent=None):
    b = QPushButton(text, parent)
    b.setProperty("role", role)
    b.style().unpolish(b)
    b.style().polish(b)
    return b


def _panel_frame(parent=None):
    f = QFrame(parent)
    f.setProperty("role", "panel")
    f.style().unpolish(f)
    f.style().polish(f)
    return f


def _h_line(parent=None):
    line = QFrame(parent)
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {BORD};")
    return line


# ── İndirme Tamamlandı Dialogu ────────────────────────────────────────────────
class DownloadDoneDialog(QDialog):
    def __init__(self, fname, folder, fsize, parent=None):
        super().__init__(parent)
        self.setWindowTitle("İndirme Tamamlandı")
        self.setFixedSize(420, 260)
        self.setModal(True)
        self._build(fname, folder, fsize)

    def _build(self, fname, folder, fsize):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Yeşil başlık
        hdr = QWidget()
        hdr.setFixedHeight(60)
        hdr.setStyleSheet(f"background: {SUCC};")
        hlay = QHBoxLayout(hdr)
        ttl = QLabel("✅  İndirme Tamamlandı")
        ttl.setStyleSheet("color: white; font-size: 14pt; font-weight: bold;")
        hlay.addWidget(ttl)

        lay.addWidget(hdr)

        body = QWidget()
        body.setStyleSheet(f"background: {PNL};")
        blay = QVBoxLayout(body)
        blay.setContentsMargins(24, 18, 24, 18)
        blay.setSpacing(10)

        for label, value in [
            ("📄  Dosya:", fname),
            ("📁  Klasör:", folder),
            ("💾  Boyut:", fsize),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {TLT}; font-size: 9pt;")
            lbl.setFixedWidth(80)
            val = QLabel(value)
            val.setStyleSheet(f"color: {TXT}; font-size: 9pt;")
            val.setWordWrap(True)
            row.addWidget(lbl)
            row.addWidget(val, 1)
            blay.addLayout(row)

        blay.addSpacing(8)

        btn_row = QHBoxLayout()
        open_btn = _btn("📂  Klasörü Aç", "gold")
        open_btn.clicked.connect(lambda: self._open_folder(folder))
        close_btn = _btn("Kapat")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(open_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        blay.addLayout(btn_row)

        lay.addWidget(body, 1)

    def _open_folder(self, folder):
        if sys.platform == "win32":
            os.startfile(folder)
        else:
            subprocess.Popen(["xdg-open", folder])


# ── Kurulum Sihirbazı ──────────────────────────────────────────────────────────
class SetupWizard(QDialog):
    setup_complete = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — İlk Kurulum")
        self.setFixedSize(560, 480)
        self.setModal(True)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Başlık
        hdr = QWidget()
        hdr.setFixedHeight(80)
        hdr.setStyleSheet(f"background: {NAV};")
        hlay = QHBoxLayout(hdr)
        hlay.setContentsMargins(24, 0, 24, 0)
        ata = QLabel("Ata")
        ata.setStyleSheet(f"color: {GOLD}; font-family: Georgia; font-size: 22pt; font-style: italic;")
        studio = QLabel(" Studio — İlk Kurulum")
        studio.setStyleSheet("color: white; font-size: 16pt; font-weight: bold;")
        hlay.addWidget(ata)
        hlay.addWidget(studio)
        hlay.addStretch()
        lay.addWidget(hdr)

        body = QWidget()
        body.setStyleSheet(f"background: {BG};")
        blay = QVBoxLayout(body)
        blay.setContentsMargins(28, 20, 28, 20)
        blay.setSpacing(12)

        blay.addWidget(_label("Hoş geldiniz! Ata Studio'yu nasıl kurmak istersiniz?",
                               size=11))

        # Seçenek 1
        self.mode_group = QButtonGroup(self)
        opt1_frame = _panel_frame()
        opt1_frame.setStyleSheet(f"QFrame[role='panel'] {{ border: 2px solid {GOLD}; }}")
        o1lay = QVBoxLayout(opt1_frame)
        o1lay.setContentsMargins(16, 12, 16, 12)
        self.rb_default = QRadioButton("⚡  Önerilen Kurulum (Hızlı)")
        self.rb_default.setChecked(True)
        self.rb_default.setStyleSheet(f"font-weight: bold; color: {NAV};")
        self.mode_group.addButton(self.rb_default, 0)
        o1lay.addWidget(self.rb_default)
        path_lbl = _label(f"📁  {DEFAULT_BASE}", size=9, color=TLT)
        path_lbl.setContentsMargins(24, 4, 0, 0)
        o1lay.addWidget(path_lbl)
        sub_lbl = _label("     📂 mp3  │  📂 wav  │  📂 mp4  │  📂 midi  │  📂 pdf  │  📂 xml",
                          size=8, color=GOLD)
        o1lay.addWidget(sub_lbl)
        blay.addWidget(opt1_frame)

        # Seçenek 2
        opt2_frame = _panel_frame()
        o2lay = QVBoxLayout(opt2_frame)
        o2lay.setContentsMargins(16, 12, 16, 12)
        self.rb_custom = QRadioButton("⚙  Özel Kurulum")
        self.rb_custom.setStyleSheet(f"font-weight: bold; color: {NAV};")
        self.mode_group.addButton(self.rb_custom, 1)
        o2lay.addWidget(self.rb_custom)
        path_row = QHBoxLayout()
        self.custom_edit = QLineEdit(DEFAULT_BASE)
        self.custom_edit.setEnabled(False)
        self.browse_btn  = _btn("…", "gold")
        self.browse_btn.setFixedWidth(36)
        self.browse_btn.setEnabled(False)
        self.browse_btn.clicked.connect(self._browse)
        path_row.addWidget(self.custom_edit)
        path_row.addWidget(self.browse_btn)
        o2lay.addLayout(path_row)
        blay.addWidget(opt2_frame)

        self.rb_custom.toggled.connect(self._on_mode)

        # Bilgi kutusu
        info = QFrame()
        info.setStyleSheet("background: #F0F0F0; border: 1px solid #CCCCCC; border-radius: 4px;")
        ilay = QHBoxLayout(info)
        ilay.setContentsMargins(12, 8, 12, 8)
        info_lbl = QLabel("ℹ  Kurulum sonrası Ayarlar sekmesinden klasör konumlarını değiştirebilirsiniz.")
        info_lbl.setStyleSheet(f"color: {NAV}; font-size: 9pt; background: transparent; border: none;")
        info_lbl.setWordWrap(True)
        ilay.addWidget(info_lbl)
        blay.addWidget(info)
        blay.addStretch()
        lay.addWidget(body, 1)

        # Alt butonlar
        foot = QWidget()
        foot.setStyleSheet(f"background: {BG2};")
        flay = QHBoxLayout(foot)
        flay.setContentsMargins(28, 14, 28, 14)
        cancel_btn = _btn("İptal")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = _btn("Kurulumu Tamamla  ▶", "gold")
        ok_btn.clicked.connect(self._complete)
        flay.addStretch()
        flay.addWidget(cancel_btn)
        flay.addSpacing(8)
        flay.addWidget(ok_btn)
        lay.addWidget(foot)

    def _on_mode(self, checked):
        self.custom_edit.setEnabled(checked)
        self.browse_btn.setEnabled(checked)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Kurulum Klasörü Seçin")
        if d:
            self.custom_edit.setText(os.path.join(d, APP_NAME))

    def _complete(self):
        base = (DEFAULT_BASE if self.rb_default.isChecked()
                else self.custom_edit.text().strip() or DEFAULT_BASE)
        try:
            dirs = create_dirs(base)
            cfg = {
                "base_dir":   base,
                "dirs":       dirs,
                "setup_done": True,
                "version":    APP_VERSION,
            }
            save_config(cfg)
            self.setup_complete.emit(cfg)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Klasörler oluşturulamadı:\n{e}")


# ── Dönüştürme Sekmesi ─────────────────────────────────────────────────────────
# Sütun indeksleri
_C_NAME   = 0
_C_SIZE   = 1
_C_DUR    = 2
_C_STATUS = 3
_C_CH     = 4
_C_NOTES  = 5
_C_MIDI   = 6
_C_XML    = 7
_C_PDF    = 8

class ConvertTab(QWidget):
    status_msg   = pyqtSignal(str)
    progress_val = pyqtSignal(int)

    def __init__(self, get_dirs, parent=None):
        super().__init__(parent)
        self.get_dirs = get_dirs
        self.workers  = []
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(14)

        # Sol
        left = QWidget()
        llay = QVBoxLayout(left)
        llay.setContentsMargins(0, 0, 0, 0)
        llay.setSpacing(8)

        hdr = QHBoxLayout()
        hdr.addWidget(_label("Dosya Listesi", bold=True, size=12, color=NAV))
        self.count_lbl = _label("0 dosya", size=9, color=TLT)
        hdr.addWidget(self.count_lbl)
        hdr.addStretch()
        add_btn       = _btn("＋ Dosya Ekle", "gold")
        folder_btn    = _btn("Klasör", "navy")
        del_btn       = _btn("✕ Sil")
        self.conv_btn = _btn("▶  Dönüştür", "gold")
        for b in (add_btn, folder_btn, del_btn, self.conv_btn):
            hdr.addWidget(b)
        llay.addLayout(hdr)

        # Tablo: 9 sütun
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["Dosya Adı", "Boyut", "Süre", "Durum",
             "Kanal", "Nota", "MIDI", "XML", "PDF"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(_C_NAME,   QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(_C_STATUS, QHeaderView.ResizeMode.Stretch)
        for col, w in [(_C_SIZE, 70), (_C_DUR, 60),
                       (_C_CH, 55),   (_C_NOTES, 60),
                       (_C_MIDI, 55), (_C_XML, 50), (_C_PDF, 50)]:
            self.table.setColumnWidth(col, w)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        self.table.cellClicked.connect(self._on_cell_click)
        llay.addWidget(self.table, 1)

        # Alt klasör butonları
        folder_row = QHBoxLayout()
        folder_row.addWidget(_label("Klasörler:", size=9, color=TLT))
        for lbl, key in [("📂 MIDI", "midi"), ("📂 XML", "xml"), ("📂 PDF", "pdf")]:
            b = _btn(lbl)
            b.setFixedHeight(24)
            b.setStyleSheet("font-size: 8pt; padding: 2px 8px;")
            b.clicked.connect(lambda _, k=key: self._open_dir(k))
            folder_row.addWidget(b)
        folder_row.addStretch()
        llay.addLayout(folder_row)

        lay.addWidget(left, 1)

        # Sağ
        right = QWidget()
        right.setFixedWidth(265)
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(0, 0, 0, 0)
        rlay.setSpacing(10)
        rlay.addWidget(self._settings_panel())
        rlay.addWidget(_label("Günlük", bold=True, size=9, color=NAV))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(200)
        rlay.addWidget(self.log_box)
        rlay.addStretch()
        lay.addWidget(right)

        add_btn.clicked.connect(self._add_files)
        folder_btn.clicked.connect(self._add_folder)
        del_btn.clicked.connect(self._remove_sel)
        self.conv_btn.clicked.connect(self._start_convert)

    def _settings_panel(self):
        frame = _panel_frame()
        flay  = QVBoxLayout(frame)
        flay.setContentsMargins(14, 10, 14, 14)
        flay.setSpacing(6)

        flay.addWidget(_label("DÖNÜŞTÜRME AYARLARI", bold=True, size=9, color=NAV))
        flay.addWidget(_h_line())

        flay.addWidget(_label("Tempo (BPM)", size=9, color=TLT))
        bpm_row = QHBoxLayout()
        self.bpm_slider = QSlider(Qt.Orientation.Horizontal)
        self.bpm_slider.setRange(40, 220)
        self.bpm_slider.setValue(120)
        self.bpm_lbl = _label("120 BPM", size=9, color=GOLD)
        self.bpm_lbl.setFixedWidth(60)
        self.bpm_slider.valueChanged.connect(
            lambda v: self.bpm_lbl.setText(f"{v} BPM"))
        bpm_row.addWidget(self.bpm_slider)
        bpm_row.addWidget(self.bpm_lbl)
        flay.addLayout(bpm_row)

        flay.addWidget(_label("Nota Hassasiyeti", size=9, color=TLT))
        onset_row = QHBoxLayout()
        self.onset_slider = QSlider(Qt.Orientation.Horizontal)
        self.onset_slider.setRange(10, 90)
        self.onset_slider.setValue(50)
        self.onset_lbl = _label("0.50", size=9, color=GOLD)
        self.onset_lbl.setFixedWidth(40)
        self.onset_slider.valueChanged.connect(
            lambda v: self.onset_lbl.setText(f"{v/100:.2f}"))
        onset_row.addWidget(self.onset_slider)
        onset_row.addWidget(self.onset_lbl)
        flay.addLayout(onset_row)

        flay.addWidget(_h_line())
        flay.addWidget(_label("UVR/MDX-Net Stem → GM Enstrüman",
                               size=8, bold=True, color=NAV))
        for stem, emoji, gm in [
            ("Vocals", "🎤", "GM:54 SynthVoice"),
            ("Bass",   "🎸", "GM:33 ElecBass"),
            ("Other",  "🎹", "GM:25 Guitar"),
            ("Drums",  "🥁", "Ch:10 Percussion"),
        ]:
            flay.addWidget(_label(
                f"{emoji} {stem}  →  {gm}", size=8, color=TMID))

        flay.addWidget(_h_line())
        self.xml_check = QCheckBox("🎼  MusicXML oluştur")
        self.xml_check.setChecked(True)
        flay.addWidget(self.xml_check)
        self.pdf_check = QCheckBox("📄  PDF nota kağıdı")
        flay.addWidget(self.pdf_check)

        return frame

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Dosya Seç", "",
            "Ses Dosyaları (*.mp3 *.wav *.flac *.ogg *.m4a);;Tümü (*)")
        for f in files:
            self._add_row(f)

    def _add_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Klasör Seç")
        if not d:
            return
        for fn in os.listdir(d):
            if fn.lower().endswith((".mp3", ".wav", ".flac", ".ogg", ".m4a")):
                self._add_row(os.path.join(d, fn))

    def _add_row(self, path):
        row = self.table.rowCount()
        self.table.insertRow(row)
        size_b = os.path.getsize(path)
        size_s = (f"{size_b/1048576:.1f} MB" if size_b > 1048576
                  else f"{size_b/1024:.0f} KB")
        vals = [os.path.basename(path), size_s, "—", "Bekliyor",
                "—", "—", "—", "—", "—"]
        for col, val in enumerate(vals):
            item = QTableWidgetItem(val)
            center = Qt.AlignmentFlag.AlignCenter
            left   = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            item.setTextAlignment(center if col not in (_C_NAME, _C_STATUS) else left)
            if col == _C_NAME:
                item.setData(Qt.ItemDataRole.UserRole, path)
            if col in (_C_MIDI, _C_XML, _C_PDF):
                item.setForeground(QColor(TLT))
            self.table.setItem(row, col, item)
        self.count_lbl.setText(f"{self.table.rowCount()} dosya")

    def _remove_sel(self):
        rows = sorted(
            {i.row() for i in self.table.selectedItems()},
            reverse=True)
        for r in rows:
            self.table.removeRow(r)
        self.count_lbl.setText(f"{self.table.rowCount()} dosya")

    def _start_convert(self):
        dirs = self.get_dirs()
        if not dirs:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce kurulumu tamamlayın.")
            return
        bpm      = self.bpm_slider.value()
        onset    = self.onset_slider.value() / 100
        make_xml = self.xml_check.isChecked()
        make_pdf = self.pdf_check.isChecked()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, _C_STATUS)
            if item and item.text() in ("Bekliyor", "—"):
                path = self.table.item(row, _C_NAME).data(Qt.ItemDataRole.UserRole)
                self._run_row(row, path, dirs, bpm, onset, make_xml, make_pdf)

    def _run_row(self, row, path, dirs, bpm, onset, make_xml, make_pdf):
        self.table.item(row, _C_STATUS).setText("⏳ İşleniyor...")
        w = ConvertWorker(path, dirs, bpm, onset, make_xml, make_pdf)
        self.workers.append(w)

        def on_progress(pct, msg):
            self.table.item(row, _C_STATUS).setText(f"{pct}% {msg}")
            self.progress_val.emit(pct)
            self.status_msg.emit(msg)

        def on_log(msg):
            self.log_box.append(msg)

        def on_done(mid, xml, pdf, ic, tn):
            self.table.item(row, _C_STATUS).setText("✅ Tamamlandı")
            self.table.item(row, _C_CH).setText(str(ic))
            self.table.item(row, _C_NOTES).setText(str(tn))
            self._set_output_cell(row, _C_MIDI, mid)
            self._set_output_cell(row, _C_XML,  xml)
            self._set_output_cell(row, _C_PDF,  pdf if make_pdf else "")
            self.status_msg.emit("Tamamlandı")
            self.progress_val.emit(100)

        def on_error(msg):
            self.table.item(row, _C_STATUS).setText(f"❌ {msg[:40]}")
            self.status_msg.emit(f"Hata: {msg}")
            QMessageBox.critical(self, "Dönüştürme Hatası", msg)

        w.progress.connect(on_progress)
        w.log.connect(on_log)
        w.done.connect(on_done)
        w.error.connect(on_error)
        w.start()

    def _set_output_cell(self, row, col, fpath):
        item = self.table.item(row, col)
        if fpath and os.path.exists(fpath):
            item.setText("✅")
            item.setData(Qt.ItemDataRole.UserRole, fpath)
            item.setForeground(QColor(SUCC))
            item.setToolTip(fpath)
        else:
            item.setText("❌")
            item.setForeground(QColor(TLT))
            item.setToolTip("")

    def _on_cell_click(self, row, col):
        if col not in (_C_MIDI, _C_XML, _C_PDF):
            return
        item = self.table.item(row, col)
        if not item:
            return
        fpath = item.data(Qt.ItemDataRole.UserRole)
        if fpath and os.path.exists(fpath):
            self._open_file(fpath)

    def _context_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        def _path(col):
            item = self.table.item(row, col)
            return item.data(Qt.ItemDataRole.UserRole) if item else None

        mid  = _path(_C_MIDI)
        xml  = _path(_C_XML)
        pdf  = _path(_C_PDF)
        src  = _path(_C_NAME)
        dirs = self.get_dirs()

        menu = QMenu(self)
        if mid and os.path.exists(mid):
            menu.addAction("🎵  MIDI Dosyasını Aç",
                           lambda: self._open_file(mid))
        if xml and os.path.exists(xml):
            menu.addAction("📄  MusicXML Dosyasını Aç",
                           lambda: self._open_file(xml))
        if pdf and os.path.exists(pdf):
            menu.addAction("📋  PDF Nota Kağıdını Aç",
                           lambda: self._open_file(pdf))
        menu.addSeparator()
        if dirs:
            menu.addAction("📂  MIDI Klasörünü Aç",
                           lambda: self._open_dir("midi"))
            menu.addAction("📂  XML Klasörünü Aç",
                           lambda: self._open_dir("xml"))
        if src:
            menu.addSeparator()
            menu.addAction("📋  Kaynak Dosya Yolunu Kopyala",
                           lambda: QApplication.clipboard().setText(src))
        if mid:
            menu.addAction("📋  MIDI Yolunu Kopyala",
                           lambda: QApplication.clipboard().setText(mid))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _open_file(self, path):
        if sys.platform == "win32":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])

    def _open_dir(self, key):
        dirs = self.get_dirs()
        if not dirs:
            return
        d = dirs.get(key, "")
        if os.path.isdir(d):
            self._open_file(d)
        else:
            QMessageBox.warning(self, "Uyarı", f"Klasör bulunamadı:\n{d}")


# ── İndir Sekmesi ─────────────────────────────────────────────────────────────
class DownloadTab(QWidget):
    status_msg   = pyqtSignal(str)
    progress_val = pyqtSignal(int)

    def __init__(self, get_dirs, parent=None):
        super().__init__(parent)
        self.get_dirs = get_dirs
        self.workers  = []
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(14)

        left = QWidget()
        llay = QVBoxLayout(left)
        llay.setContentsMargins(0, 0, 0, 0)
        llay.setSpacing(8)

        hdr = QHBoxLayout()
        hdr.addWidget(_label("URL / Arama Listesi", bold=True, size=12, color=NAV))
        hdr.addStretch()
        del_btn = _btn("✕ Sil")
        hdr.addWidget(del_btn)
        llay.addLayout(hdr)

        # URL giriş satırı
        url_row = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText(
            "YouTube/Spotify/SoundCloud linki veya arama metni girin...")
        paste_btn = _btn("📋 Panodan Al")
        add_btn   = _btn("＋ Ekle", "gold")
        url_row.addWidget(self.url_edit, 1)
        url_row.addWidget(paste_btn)
        url_row.addWidget(add_btn)
        llay.addLayout(url_row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["URL / Sorgu", "Format", "Durum", ""])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(3, 90)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        llay.addWidget(self.table, 1)

        llay.addWidget(_label(
            "Desteklenen: YouTube, Spotify, SoundCloud, düz metin araması",
            size=9, color=TLT))

        lay.addWidget(left, 1)

        # Sağ: ayarlar + log
        right = QWidget()
        right.setFixedWidth(265)
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(0, 0, 0, 0)
        rlay.setSpacing(10)

        settings = self._settings_panel()
        rlay.addWidget(settings)

        rlay.addWidget(_label("Günlük", bold=True, size=9, color=NAV))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(220)
        rlay.addWidget(self.log_box)
        rlay.addStretch()

        lay.addWidget(right)

        # Bağlantılar
        paste_btn.clicked.connect(self._paste)
        add_btn.clicked.connect(self._add_url)
        del_btn.clicked.connect(self._remove_sel)
        self.url_edit.returnPressed.connect(self._add_url)
        self.dl_btn.clicked.connect(self._start_download)

    def _settings_panel(self):
        frame = _panel_frame()
        flay  = QVBoxLayout(frame)
        flay.setContentsMargins(14, 10, 14, 14)
        flay.setSpacing(8)

        flay.addWidget(_label("İNDİRME AYARLARI", bold=True, size=9, color=NAV))
        flay.addWidget(_h_line())

        flay.addWidget(_label("Format", size=9, color=TLT))
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["mp3", "wav", "mp4"])
        flay.addWidget(self.fmt_combo)

        flay.addWidget(_label("Kalite", size=9, color=TLT))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["En İyi", "Yüksek", "Orta", "Düşük"])
        flay.addWidget(self.quality_combo)

        flay.addWidget(_h_line())
        self.dl_btn = _btn("⬇  İndir", "gold")
        flay.addWidget(self.dl_btn)

        return frame

    def _paste(self):
        clip = QApplication.clipboard().text().strip()
        if clip:
            self.url_edit.setText(clip)

    def _add_url(self):
        url = self.url_edit.text().strip()
        if not url:
            return
        row = self.table.rowCount()
        self.table.insertRow(row)
        fmt = self.fmt_combo.currentText()
        for col, val in enumerate([url, fmt, "Bekliyor", ""]):
            item = QTableWidgetItem(val)
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
                if col != 0 else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, col, item)
        self.url_edit.clear()

    def _remove_sel(self):
        rows = sorted(
            {i.row() for i in self.table.selectedItems()},
            reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def _start_download(self):
        dirs = self.get_dirs()
        if not dirs:
            QMessageBox.warning(self, "Uyarı",
                "Lütfen önce kurulumu tamamlayın.")
            return
        for row in range(self.table.rowCount()):
            status = self.table.item(row, 2).text()
            if status in ("Bekliyor", "—"):
                url = self.table.item(row, 0).text()
                fmt = self.table.item(row, 1).text()
                quality = self.quality_combo.currentText()
                self._run_row(row, url, dirs, fmt, quality)

    def _run_row(self, row, url, dirs, fmt, quality):
        self.table.item(row, 2).setText("⏳ Başlıyor...")
        before = set()
        out_dir = dirs.get(fmt, dirs.get("mp3", ""))
        if os.path.isdir(out_dir):
            before = set(os.listdir(out_dir))

        w = DownloadWorker(url, dirs, fmt, quality)
        self.workers.append(w)

        def on_progress(pct, msg):
            self.table.item(row, 2).setText(f"{pct}% {msg}")
            self.progress_val.emit(pct)
            self.status_msg.emit(msg)

        def on_log(msg):
            self.log_box.append(msg)

        def on_done():
            self.table.item(row, 2).setText("✅ Tamamlandı")
            self.status_msg.emit("İndirme tamamlandı")
            self.progress_val.emit(100)
            after = set(os.listdir(out_dir)) if os.path.isdir(out_dir) else set()
            new_files = after - before
            if new_files:
                fname = sorted(new_files)[-1]
                fpath = os.path.join(out_dir, fname)
                fsize_b = os.path.getsize(fpath)
                fsize_s = (f"{fsize_b/1048576:.1f} MB" if fsize_b > 1048576
                           else f"{fsize_b/1024:.0f} KB")
                dlg = DownloadDoneDialog(fname, out_dir, fsize_s, self)
                dlg.exec()

        def on_error(msg):
            self.table.item(row, 2).setText(f"❌ {msg[:40]}")
            self.status_msg.emit(f"Hata: {msg}")
            QMessageBox.critical(self, "İndirme Başarısız",
                f"{msg}\n\nÇözüm: Chrome'da ilgili platforma giriş yapın "
                "ve tekrar deneyin.")

        w.progress.connect(on_progress)
        w.log.connect(on_log)
        w.done.connect(on_done)
        w.error.connect(on_error)
        w.start()


# ── Keşfet Sekmesi ────────────────────────────────────────────────────────────
class LiveStreamTab(QWidget):
    """
    Keşfet sekmesi — Hafif clipboard monitor tabanlı indirici.
    Platform butonları varsayılan tarayıcıda açılır.
    Kullanıcı URL kopyaladığında otomatik algılanır.
    """
    status_msg   = pyqtSignal(str)
    progress_val = pyqtSignal(int)

    PLATFORMS = [
        ("▶  YouTube",    "https://www.youtube.com"),
        ("🎵  Spotify",   "https://open.spotify.com"),
        ("☁  SoundCloud", "https://soundcloud.com"),
        ("✕  X/Twitter",  "https://x.com"),
        ("📷  Instagram",  "https://www.instagram.com"),
        ("♪  TikTok",     "https://www.tiktok.com"),
        ("👥  Facebook",   "https://www.facebook.com"),
    ]

    # Bu kalıplardan biri panoda varsa otomatik algıla
    # Son kural → yt-dlp'nin desteklediği 1740+ platform dahil her HTTP/HTTPS URL'i yakala
    URL_PATTERNS = [
        r"youtube\.com/watch",
        r"youtu\.be/",
        r"youtube\.com/shorts",
        r"open\.spotify\.com/",
        r"soundcloud\.com/",
        r"tiktok\.com/",
        r"instagram\.com/",
        r"twitter\.com/",
        r"x\.com/",
        r"facebook\.com/",
        r"vimeo\.com/",
        r"dailymotion\.com/",
        r"twitch\.tv/",
        r"bilibili\.com/",
        r"rumble\.com/",
        r"odysee\.com/",
        r"bandcamp\.com/",
        r"mixcloud\.com/",
        r"deezer\.com/",
        r"https?://",    # ← evrensel fallback: diğer tüm http(s) URL'leri yakala
    ]

    def __init__(self, get_dirs, parent=None):
        super().__init__(parent)
        self.get_dirs      = get_dirs
        self.workers       = []
        self._last_clip    = ""
        self._monitor_on   = False
        self._build()
        self._start_monitor()

    # ------------------------------------------------------------------ UI ---
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._make_platform_bar())
        lay.addWidget(self._make_url_bar())
        lay.addWidget(self._make_info_area(), 1)
        lay.addWidget(self._make_bottom_bar())

    def _make_platform_bar(self):
        bar = QWidget()
        bar.setStyleSheet(f"background:{BG2}; border-bottom:1px solid {BORD};")
        vlay = QVBoxLayout(bar)
        vlay.setContentsMargins(14, 10, 14, 10)
        vlay.setSpacing(6)

        vlay.addWidget(_label("Platform Seç  →  Tarayıcında Aç  →  URL Kopyala  →  Otomatik Algıla",
                               size=9, color=TLT))

        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        for i, (label, url) in enumerate(self.PLATFORMS):
            btn = _btn(label, "platform")
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda _, u=url: self._open_browser(u))
            (row1 if i < 4 else row2).addWidget(btn)
        row1.addStretch()
        row2.addStretch()
        vlay.addLayout(row1)
        vlay.addLayout(row2)
        return bar

    def _make_url_bar(self):
        bar = QWidget()
        bar.setStyleSheet(f"background:{PNL}; border-bottom:1px solid {BORD};")
        hlay = QHBoxLayout(bar)
        hlay.setContentsMargins(12, 8, 12, 8)
        hlay.setSpacing(8)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText(
            "URL buraya otomatik gelir — ya da elle yapıştır / arama metni yaz...")
        self.url_edit.setFixedHeight(32)
        self.url_edit.returnPressed.connect(self._trigger_download)
        hlay.addWidget(self.url_edit, 1)

        paste_btn = _btn("📋  Panodan Al", "navy")
        paste_btn.setFixedHeight(32)
        paste_btn.setFixedWidth(120)
        paste_btn.clicked.connect(self._manual_paste)
        hlay.addWidget(paste_btn)

        return bar

    def _make_info_area(self):
        """Kullanım rehberi + son indirilenler."""
        w = QWidget()
        w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)

        # Adım adım rehber
        guide = _panel_frame()
        glay  = QVBoxLayout(guide)
        glay.setContentsMargins(22, 16, 22, 16)
        glay.setSpacing(10)
        glay.addWidget(_label("Nasıl Kullanılır?", bold=True, size=11, color=NAV))
        glay.addWidget(_h_line())

        steps = [
            ("1", "Yukarıdan bir platform butonuna tıkla",
                  "Tarayıcında açılır, giriş yapabilirsin"),
            ("2", "İstediğin video / şarkı sayfasına git",
                  "YouTube, Spotify, Vimeo, Twitch, Bilibili ve 1740+ platform..."),
            ("3", "Adres çubuğundaki URL'yi kopyala  (Ctrl+C)",
                  "Ata Studio arka planda otomatik algılar 🔔"),
            ("4", "Programa dön — URL zaten hazır!",
                  "İndir butonuna bas, gerisini biz hallederiz ✅"),
        ]
        for num, title, sub in steps:
            row = QHBoxLayout()
            num_lbl = QLabel(num)
            num_lbl.setFixedSize(28, 28)
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_lbl.setStyleSheet(
                f"background:#1A1A1A; color:white; font-weight:bold; "
                f"font-size:11pt; border-radius:14px;")
            col = QVBoxLayout()
            col.setSpacing(1)
            col.addWidget(_label(title, bold=True, size=10, color=NAV))
            col.addWidget(_label(sub, size=9, color=TLT))
            row.addWidget(num_lbl)
            row.addSpacing(10)
            row.addLayout(col, 1)
            glay.addLayout(row)

        lay.addWidget(guide)

        # Clipboard monitor durumu
        self.monitor_lbl = _label(
            "🟢  Clipboard Monitor Aktif — URL kopyaladığında otomatik algılanır",
            size=9, color=SUCC)
        self.monitor_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.monitor_lbl)
        lay.addStretch()

        return w

    def _make_bottom_bar(self):
        bar = QWidget()
        bar.setStyleSheet(f"background:{NAV}; border-top:1px solid #162230;")
        hlay = QHBoxLayout(bar)
        hlay.setContentsMargins(12, 6, 12, 6)
        hlay.setSpacing(8)

        self.ls_status = _label("Hazır — platform seç ve URL kopyala",
                                  size=9, color=TLT)
        self.ls_status.setStyleSheet(f"color:{TLT}; background:transparent;")
        hlay.addWidget(self.ls_status, 1)

        self.ls_progress = QProgressBar()
        self.ls_progress.setFixedWidth(160)
        self.ls_progress.setFixedHeight(5)
        self.ls_progress.setTextVisible(False)
        self.ls_progress.setVisible(False)
        self.ls_progress.setStyleSheet(
            f"QProgressBar{{background:#2A3F55;border:none;border-radius:2px;}}"
            f"QProgressBar::chunk{{background:#1A1A1A;border-radius:2px;}}")
        hlay.addWidget(self.ls_progress)

        hlay.addWidget(_label("Format:", size=9, color=TLT))
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["mp3", "wav", "mp4"])
        self.fmt_combo.setFixedWidth(68)
        self.fmt_combo.setFixedHeight(26)
        hlay.addWidget(self.fmt_combo)

        hlay.addWidget(_label("Kalite:", size=9, color=TLT))
        self.qual_combo = QComboBox()
        self.qual_combo.addItems(["En İyi", "Yüksek", "Orta"])
        self.qual_combo.setFixedWidth(80)
        self.qual_combo.setFixedHeight(26)
        hlay.addWidget(self.qual_combo)

        self.dl_btn = _btn("⬇  İndir", "gold")
        self.dl_btn.setFixedHeight(30)
        self.dl_btn.clicked.connect(self._trigger_download)
        hlay.addWidget(self.dl_btn)

        return bar

    # ----------------------------------------------- Clipboard Monitor -------
    def _start_monitor(self):
        self._timer = QTimer(self)
        self._timer.setInterval(600)          # 600ms'de bir kontrol
        self._timer.timeout.connect(self._check_clipboard)
        self._timer.start()
        self._monitor_on = True

    def _check_clipboard(self):
        try:
            clip = QApplication.clipboard().text().strip()
        except Exception:
            return
        if clip == self._last_clip or not clip:
            return
        self._last_clip = clip

        # Desteklenen platform URL'si mi?
        for pattern in self.URL_PATTERNS:
            if re.search(pattern, clip):
                self._on_url_detected(clip)
                break

    def _on_url_detected(self, url: str):
        """Panoda herhangi bir URL algılandı — yt-dlp 1740+ platform destekler."""
        self.url_edit.setText(url)

        # Platformu tespit et (bilinmeyen = evrensel yt-dlp desteği)
        platform = "Evrensel"
        for name, base in [
            ("YouTube",     "youtube"),    ("Spotify",     "spotify"),
            ("SoundCloud",  "soundcloud"), ("TikTok",      "tiktok"),
            ("Instagram",   "instagram"),  ("Twitter",     "twitter"),
            ("X",           "x.com"),      ("Facebook",    "facebook"),
            ("Vimeo",       "vimeo"),      ("Dailymotion", "dailymotion"),
            ("Twitch",      "twitch"),     ("Bilibili",    "bilibili"),
            ("Rumble",      "rumble"),     ("Odysee",      "odysee"),
            ("Bandcamp",    "bandcamp"),   ("Mixcloud",    "mixcloud"),
            ("Deezer",      "deezer"),
        ]:
            if base in url.lower():
                platform = name
                break

        short = url[:55] + "..." if len(url) > 55 else url
        self.ls_status.setText(f"🔔  {platform} linki algılandı!")
        self.status_msg.emit(f"{platform} linki algılandı")
        self.monitor_lbl.setText(
            f"🔔  {platform} linki yakalandı → İndir butonuna bas!")
        self.monitor_lbl.setStyleSheet(f"color:{GOLD}; font-weight:bold;")

    # -------------------------------------------------------- Tarayıcı --------
    def _open_browser(self, url: str):
        webbrowser.open(url)
        self.ls_status.setText(f"Tarayıcıda açıldı: {url}")
        self.status_msg.emit(f"Tarayıcıda açıldı")

    def _manual_paste(self):
        clip = QApplication.clipboard().text().strip()
        if clip:
            self.url_edit.setText(clip)
            self._last_clip = clip
            self.ls_status.setText("URL alındı — İndir butonuna basabilirsin")

    # ------------------------------------------------------------ İndir -------
    def _trigger_download(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Uyarı",
                "URL boş!\nBir platform seç, sayfaya git ve URL\'yi kopyala.")
            return
        dirs = self.get_dirs()
        if not dirs:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce kurulumu tamamlayın.")
            return

        fmt     = self.fmt_combo.currentText()
        quality = self.qual_combo.currentText()
        out_dir = dirs.get(fmt, dirs.get("mp3", ""))
        before  = set(os.listdir(out_dir)) if os.path.isdir(out_dir) else set()

        self.dl_btn.setEnabled(False)
        self.ls_progress.setVisible(True)
        self.ls_progress.setValue(0)
        self.ls_status.setText("⏳ İndirme başlıyor...")
        self.status_msg.emit("İndirme başlıyor...")
        self.monitor_lbl.setText(
            "🟡  İndirme devam ediyor — clipboard monitor duraklatıldı")
        self.monitor_lbl.setStyleSheet(f"color:{GOLD};")
        self._timer.stop()   # İndirme sırasında monitor'ü durdur

        w = DownloadWorker(url, dirs, fmt, quality)
        self.workers.append(w)

        def on_progress(pct, msg):
            self.ls_progress.setValue(pct)
            self.ls_status.setText(msg)
            self.progress_val.emit(pct)
            self.status_msg.emit(msg)

        def on_done():
            self.dl_btn.setEnabled(True)
            self.ls_progress.setVisible(False)
            self.ls_status.setText("✅ İndirme tamamlandı!")
            self.progress_val.emit(100)
            self.url_edit.clear()
            self._last_clip = ""
            self.monitor_lbl.setText(
                "🟢  Clipboard Monitor Aktif — URL kopyaladığında otomatik algılanır")
            self.monitor_lbl.setStyleSheet(f"color:{SUCC};")
            self._timer.start()   # Monitor'ü yeniden başlat

            after     = set(os.listdir(out_dir)) if os.path.isdir(out_dir) else set()
            new_files = after - before
            if new_files:
                fname   = sorted(new_files)[-1]
                fpath   = os.path.join(out_dir, fname)
                fsize_b = os.path.getsize(fpath)
                fsize_s = (f"{fsize_b/1048576:.1f} MB" if fsize_b > 1048576
                           else f"{fsize_b/1024:.0f} KB")
                dlg = DownloadDoneDialog(fname, out_dir, fsize_s, self)
                dlg.exec()

        def on_error(msg):
            self.dl_btn.setEnabled(True)
            self.ls_progress.setVisible(False)
            self.ls_status.setText(f"❌ Hata: {msg[:60]}")
            self.status_msg.emit(f"Hata: {msg[:60]}")
            self.monitor_lbl.setText(
                "🟢  Clipboard Monitor Aktif — URL kopyaladığında otomatik algılanır")
            self.monitor_lbl.setStyleSheet(f"color:{SUCC};")
            self._timer.start()
            QMessageBox.critical(self, "İndirme Başarısız",
                f"{msg}\n\nÇözüm: Tarayıcında platforma giriş yap ve tekrar dene.")

        w.progress.connect(on_progress)
        w.done.connect(on_done)
        w.error.connect(on_error)
        w.start()


# ── Ayarlar Sekmesi ────────────────────────────────────────────────────────────
class SettingsTab(QWidget):
    def __init__(self, get_cfg, save_cfg_fn, parent=None):
        super().__init__(parent)
        self.get_cfg      = get_cfg
        self.save_cfg_fn  = save_cfg_fn
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        outer_lay = QVBoxLayout(self)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        lay = QVBoxLayout(content)
        lay.setContentsMargins(24, 20, 24, 24)
        lay.setSpacing(16)

        # Ana klasör
        section = self._make_section("📁  Çıktı Klasörleri")
        slay    = section.layout()

        cfg  = self.get_cfg()
        dirs = cfg.get("dirs", DEFAULT_DIRS)

        self.dir_edits = {}
        for key, default in DEFAULT_DIRS.items():
            row = QHBoxLayout()
            row.addWidget(_label(f"{key.upper()}:", size=9, color=TLT, parent=content))
            edit = QLineEdit(dirs.get(key, default))
            edit.setReadOnly(True)
            browse = _btn("…", "gold")
            browse.setFixedWidth(36)
            browse.clicked.connect(lambda _, k=key, e=edit: self._browse_dir(k, e))
            row.addWidget(edit, 1)
            row.addWidget(browse)
            slay.addLayout(row)
            self.dir_edits[key] = edit

        save_btn = _btn("💾  Klasörleri Kaydet", "gold")
        save_btn.setFixedWidth(180)
        save_btn.clicked.connect(self._save_dirs)
        slay.addWidget(save_btn)

        lay.addWidget(section)

        # Klasör oluştur
        section2 = self._make_section("🔧  Klasör İşlemleri")
        s2lay    = section2.layout()
        create_btn = _btn("📂  Tüm Klasörleri Oluştur", "navy")
        create_btn.setFixedWidth(200)
        create_btn.clicked.connect(self._create_all_dirs)
        s2lay.addWidget(create_btn)
        open_btn = _btn("🗂  Ana Klasörü Aç")
        open_btn.setFixedWidth(160)
        open_btn.clicked.connect(self._open_base)
        s2lay.addWidget(open_btn)
        lay.addWidget(section2)

        # ── Proxy / VPN Ayarı ──────────────────────────────────────────
        section3 = self._make_section("🌐  Proxy Ayarı  (Engelli Siteler İçin)")
        s3lay    = section3.layout()

        s3lay.addWidget(_label(
            "Türkiye'de engelli siteler için proxy kullan (ör: socks5://127.0.0.1:1080)",
            size=9, color=TLT, parent=content))

        proxy_row = QHBoxLayout()
        proxy_row.addWidget(_label("Proxy:", size=9, color=TLT, parent=content))
        self.proxy_edit = QLineEdit(cfg.get("proxy", ""))
        self.proxy_edit.setPlaceholderText(
            "socks5://127.0.0.1:1080  veya  http://127.0.0.1:8080  (boş = proxy yok)")
        self.proxy_edit.setFixedHeight(30)
        proxy_row.addWidget(self.proxy_edit, 1)
        s3lay.addLayout(proxy_row)

        proxy_hint = QHBoxLayout()
        for label, val in [("Tor", "socks5://127.0.0.1:9050"),
                           ("Clash", "http://127.0.0.1:7890"),
                           ("V2Ray", "socks5://127.0.0.1:10808")]:
            btn = _btn(label, "navy")
            btn.setFixedHeight(24)
            btn.setFixedWidth(72)
            btn.clicked.connect(lambda _, v=val: self.proxy_edit.setText(v))
            proxy_hint.addWidget(btn)
        proxy_hint.addStretch()
        s3lay.addLayout(proxy_hint)

        save_proxy_btn = _btn("💾  Proxy Kaydet", "gold")
        save_proxy_btn.setFixedWidth(150)
        save_proxy_btn.clicked.connect(self._save_proxy)
        s3lay.addWidget(save_proxy_btn)

        lay.addWidget(section3)
        lay.addStretch()

    def _save_proxy(self):
        cfg = self.get_cfg()
        cfg["proxy"] = self.proxy_edit.text().strip()
        self.save_cfg_fn(cfg)
        msg = f"Proxy kaydedildi: {cfg['proxy']}" if cfg["proxy"] else "Proxy temizlendi (direkt bağlantı)"
        QMessageBox.information(self, "Kaydedildi", msg)

    def _make_section(self, title):
        frame = _panel_frame()
        lay   = QVBoxLayout(frame)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(10)
        hdr = _label(title, bold=True, size=10, color=NAV)
        lay.addWidget(hdr)
        lay.addWidget(_h_line())
        return frame

    def _browse_dir(self, key, edit):
        d = QFileDialog.getExistingDirectory(self, f"{key.upper()} Klasörü Seç")
        if d:
            edit.setText(d)

    def _save_dirs(self):
        cfg  = self.get_cfg()
        dirs = cfg.get("dirs", {})
        for key, edit in self.dir_edits.items():
            dirs[key] = edit.text()
        cfg["dirs"] = dirs
        self.save_cfg_fn(cfg)
        for d in dirs.values():
            os.makedirs(d, exist_ok=True)
        QMessageBox.information(self, "Kaydedildi",
            "Klasör ayarları kaydedildi ve oluşturuldu.")

    def _create_all_dirs(self):
        cfg  = self.get_cfg()
        dirs = cfg.get("dirs", DEFAULT_DIRS)
        for d in dirs.values():
            os.makedirs(d, exist_ok=True)
        QMessageBox.information(self, "Tamam",
            "Tüm klasörler oluşturuldu.")

    def _open_base(self):
        cfg  = self.get_cfg()
        base = cfg.get("base_dir", DEFAULT_BASE)
        if os.path.isdir(base):
            if sys.platform == "win32":
                os.startfile(base)
            else:
                subprocess.Popen(["xdg-open", base])
        else:
            QMessageBox.warning(self, "Uyarı",
                f"Klasör bulunamadı:\n{base}")


# ── Ana Pencere ────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1100, 740)
        self.setMinimumSize(900, 620)
        self._cfg      = {}
        self._out_dirs = {}

        self._setup_ui()

        cfg = load_config()
        if cfg.get("setup_done"):
            self._init_app(cfg)
        else:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(200, self._show_setup)

    def _setup_ui(self):
        # main_progress sekme widget'larından önce tanımlanmalı
        self.main_progress = QProgressBar()
        self.status_lbl    = QLabel("Hazır")

        # Merkezi widget
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Üst şerit (siyah header + kartal)
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet(f"background: {NAV};")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 28, 0)
        h_lay.setSpacing(0)

        # Kartal görseli
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import QByteArray
        import base64 as _b64
        eagle_lbl = QLabel()
        eagle_data = _b64.b64decode(EAGLE_B64)
        eagle_pix  = QPixmap()
        eagle_pix.loadFromData(QByteArray(eagle_data))
        eagle_lbl.setPixmap(eagle_pix)
        eagle_lbl.setFixedSize(104, 70)
        eagle_lbl.setScaledContents(True)
        eagle_lbl.setStyleSheet("background: transparent;")
        h_lay.addWidget(eagle_lbl)
        h_lay.addSpacing(10)

        # Başlık metinleri
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.setContentsMargins(0, 0, 0, 0)

        name_row = QHBoxLayout()
        name_row.setSpacing(0)
        ata_lbl = QLabel("Ata")
        ata_lbl.setStyleSheet(
            "color: white; font-family: Georgia; font-size: 24pt; "
            "font-style: italic; font-weight: bold; background: transparent;")
        studio_lbl = QLabel(" Studio")
        studio_lbl.setStyleSheet(
            "color: #CCCCCC; font-size: 20pt; font-weight: 300; background: transparent;")
        name_row.addWidget(ata_lbl)
        name_row.addWidget(studio_lbl)
        name_row.addStretch()

        sub_lbl = QLabel(f"v{APP_VERSION}  ·  MP3 → MIDI · XML · PDF  ·  1740+ Platform İndirici")
        sub_lbl.setStyleSheet(
            "color: #666666; font-size: 8pt; letter-spacing: 1px; background: transparent;")

        title_col.addStretch()
        title_col.addLayout(name_row)
        title_col.addWidget(sub_lbl)
        title_col.addStretch()

        h_lay.addLayout(title_col, 1)
        main_lay.addWidget(header)

        # Tab çubuğu
        tab_bar = QWidget()
        tab_bar.setStyleSheet(f"background: {BG2}; border-bottom: 1px solid {BORD};")
        tab_lay = QHBoxLayout(tab_bar)
        tab_lay.setContentsMargins(16, 0, 16, 0)
        tab_lay.setSpacing(0)

        self._tab_btns  = []
        self._tab_stack = QStackedWidget()
        self._tab_stack.setStyleSheet(f"background: {BG};")

        tab_defs = [
            ("🎵  Dönüştür",  self._make_convert_tab),
            ("📥  İndir",     self._make_download_tab),
            ("🔍  Keşfet",    self._make_livestream_tab),
            ("⚙  Ayarlar",   self._make_settings_tab),
        ]

        for i, (label, builder) in enumerate(tab_defs):
            btn = QPushButton(label)
            btn.setProperty("role", "tab")
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            self._tab_btns.append(btn)
            tab_lay.addWidget(btn)
            widget = builder()
            self._tab_stack.addWidget(widget)

        tab_lay.addStretch()
        main_lay.addWidget(tab_bar)
        main_lay.addWidget(self._tab_stack, 1)

        # Alt çubuk
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(28)
        bottom_bar.setStyleSheet(
            f"background: {NAV}; border-top: 1px solid #162230;")
        bot_lay = QHBoxLayout(bottom_bar)
        bot_lay.setContentsMargins(14, 0, 14, 0)
        bot_lay.setSpacing(10)

        self.status_lbl.setStyleSheet(
            f"color: {TLT}; font-size: 9pt; background: transparent;")
        bot_lay.addWidget(self.status_lbl, 1)

        self.main_progress.setFixedWidth(180)
        self.main_progress.setFixedHeight(6)
        self.main_progress.setTextVisible(False)
        self.main_progress.setStyleSheet(
            f"QProgressBar {{ background: #222222; border: none; border-radius: 3px; }}"
            f"QProgressBar::chunk {{ background: #1A1A1A; border-radius: 3px; }}")
        bot_lay.addWidget(self.main_progress)

        main_lay.addWidget(bottom_bar)

    def _make_convert_tab(self):
        w = ConvertTab(self._get_dirs)
        w.status_msg.connect(self._set_status)
        w.progress_val.connect(self.main_progress.setValue)
        self._convert_tab = w
        return w

    def _make_download_tab(self):
        w = DownloadTab(self._get_dirs)
        w.status_msg.connect(self._set_status)
        w.progress_val.connect(self.main_progress.setValue)
        self._download_tab = w
        return w

    def _make_livestream_tab(self):
        w = LiveStreamTab(self._get_dirs)
        w.status_msg.connect(self._set_status)
        w.progress_val.connect(self.main_progress.setValue)
        self._livestream_tab = w
        return w

    def _make_settings_tab(self):
        w = SettingsTab(self._get_cfg, self._save_cfg)
        self._settings_tab = w
        return w

    def _switch_tab(self, idx):
        for i, btn in enumerate(self._tab_btns):
            btn.setChecked(i == idx)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._tab_stack.setCurrentIndex(idx)

    def _set_status(self, msg):
        self.status_lbl.setText(msg)

    def _get_dirs(self):
        return self._out_dirs

    def _get_cfg(self):
        return self._cfg

    def _save_cfg(self, cfg):
        self._cfg      = cfg
        self._out_dirs = cfg.get("dirs", DEFAULT_DIRS)
        save_config(cfg)

    def _show_setup(self):
        dlg = SetupWizard(self)
        dlg.setup_complete.connect(self._init_app)
        dlg.exec()

    def _init_app(self, cfg):
        self._cfg      = cfg
        self._out_dirs = cfg.get("dirs", DEFAULT_DIRS)
        for d in self._out_dirs.values():
            os.makedirs(d, exist_ok=True)
        self._set_status("Hazır")


# ── Giriş noktası ─────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)

    win = MainWindow()
    win.show()

    # Pencereyi ortala
    screen = app.primaryScreen().geometry()
    fg     = win.frameGeometry()
    fg.moveCenter(screen.center())
    win.move(fg.topLeft())

    sys.exit(app.exec())


if __name__ == "__main__":
    main()