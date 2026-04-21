# 🦅 Ata Studio v5.0

**MP3 → MIDI · XML · PDF Dönüştürücü & 1740+ Platform Evrensel İndirici**

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green?style=flat-square)
![yt-dlp](https://img.shields.io/badge/yt--dlp-2026.03+-orange?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## ✨ Özellikler

### 🎵 Dönüştürücü
- MP3 / WAV → MIDI dönüştürme
- MIDI → MusicXML (MuseScore 4 entegrasyonu)
- MusicXML → PDF (LilyPond entegrasyonu)
- Ses ayırma — vokal / enstrüman (audio-separator)

### 📥 Evrensel İndirici
- **1740+ platform** desteği (yt-dlp tabanlı)
- YouTube, Spotify, SoundCloud, TikTok, Instagram, Vimeo, Twitch, Bilibili ve daha fazlası
- MP3 / WAV / MP4 format seçimi

### 🔍 Keşfet Sekmesi
- Clipboard monitor — URL kopyaladığında **otomatik** algılar
- Platform hızlı erişim butonları

### ⚙️ Ayarlar
- Çıktı klasörü yapılandırması
- Proxy ayarı (engelli siteler için)

---

## 🚀 Kurulum

### Hazır Exe (Windows — Önerilen)
1. [Releases](../../releases) sayfasından `AtaStudio_v5.0_Setup.exe` indir
2. Kurulum sihirbazını çalıştır
3. Başlat!

### Kaynaktan Çalıştır

```bash
git clone https://github.com/ataeyvaz/AtaStudio.git
cd AtaStudio

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
python atastudio.py
```

### Exe Build

```bash
pip install pyinstaller pillow
python build.py
```

---

## 📋 Gereksinimler

| Yazılım | Sürüm | Zorunlu |
|---|---|---|
| Python | 3.11+ | ✅ |
| FFmpeg | Herhangi | ✅ |
| MuseScore 4 | 4.x | ⬜ XML/PDF için |
| LilyPond | 2.x | ⬜ PDF için |

---

## 📜 Lisans

MIT License

---

## 🙏 Teşekkür

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — Evrensel indirici motoru
- [PyQt6](https://riverbankcomputing.com/software/pyqt/) — Arayüz framework
- [audio-separator](https://github.com/nomadkaraoke/python-audio-separator) — Ses ayırma
- [MuseScore](https://musescore.org) — Nota yazılımı
- [FFmpeg](https://ffmpeg.org) — Ses/video işleme