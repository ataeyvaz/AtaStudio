# Ata Studio — süreç ve durum (2026-10-07)

Kalıcı kurallar için `CLAUDE.md` (henüz yok). Bu dosya: nerede kaldık, nasıl çalışıyoruz, sırada ne var.

> **Not:** Bu belge önceki oturumlar hatırlanarak değil, repodan (git geçmişi, kod, README, build dosyaları) çıkarılarak yazıldı. Koddan doğrulanamayan şeyler "belirsiz" diye işaretli.

## 1. Neredeyiz
Proje: PyQt6 masaüstü uygulaması (Windows), tek dosya `atastudio.py` (~3350 satır). Repo: https://github.com/ataeyvaz/AtaStudio

| İş / modül | Hedef | Yapılan | Durum |
|---|---|---|---|
| Dönüştürücü (ConvertTab) | MP3/WAV → MIDI → XML → PDF, ses ayırma | v5.0'dan beri var; model seçici (MDX/Demucs/BS-Roformer) eklendi, yavaş CPU modelleri için uyarı diyaloğu | ✅ |
| İndirici (DownloadTab) | yt-dlp ile 1740+ platform | v5.0'dan beri var | ✅ |
| Keşfet / gömülü browser | QtWebEngine ile site gezme | Eklendi (f559b5b). Log'da WebEngine önbellek hataları var (aşağıda) | 🟡 |
| Loopback ses kaydı (RecordTab) | Sistem sesini kaydet, MP3/WAV | Kayıt, süre/isim diyaloğu, floating buton, system tray eklendi | 🟡 MP3 dönüşümü geri açıldı, gerçek kayıtla denenmedi |
| Canlı yayın (LiveStreamTab) | | Kodda var; kapsamı belirsiz | ❓ |
| Kurulum paketi | Inno Setup ile Setup.exe | `setup.iss` v6.0, `installer/` içinde v5.0 ve v6.0 Setup.exe mevcut | ✅ |

Son commit: `2a12a0a` (2026-10-07, push edildi) · Testler: yok (otomatik test dosyası bulunmuyor).

## 2. Sıradaki işler (öncelik sırasıyla)
1. **Kayıt MP3 dönüşümünü gerçek kayıtla dene** (2026-10-07'de geri açıldı: `_find_ffmpeg()` ile ffmpeg bulunuyor, başarısızsa WAV'a düşüp uyarı veriyor; debug print'ler silindi). Paketli exe'de ffmpeg'in bulunduğunu da doğrula.
2. ~~ffmpeg yolu~~ — sabit yol kaldırıldı, `_find_ffmpeg()` (exe içi → uygulama klasörü → PATH).
3. **Sürüm tutarsızlığı:** `APP_VERSION = "6.0"` ama dosya başlığı, `build.py` ve README hâlâ "v5.0". Hepsini 6.0'a çek.
4. **README'yi güncelle:** loopback kayıt, gömülü browser, floating buton, tray özellikleri README'de yok.
5. **CLAUDE.md oluştur** (kalıcı kurallar: dosya yapısı, yasaklar).
6. WebEngine önbellek hatasını incele (`convert_log.txt`).

## 3. Çalışma sistemi (her adımda)
1. Önce bu dosyayı oku, kaldığın yerden devam et.
2. Kod değişikliğini `atastudio.py` içinde yap; sabit kullanıcı yolu (`C:\Users\Ata\…`) ekleme.
3. Çalıştırıp dene: `python atastudio.py` (venv içinde).
4. Bu dosyayı güncelle.
5. Commit — yalnızca kullanıcı isterse. Exe/log dosyaları commit'e girmez (`.gitignore`'da).

## 4. Kararlar (tarihli)
- 2026-10-07: `ffmpeg.exe`, `ffplay.exe`, `ffprobe.exe`, `convert_log.txt` ve bozuk adlı `record tab_dump.txt` `.gitignore`'a alındı — exe'ler ~200 MB'ar, repoya girmemeli.
- 2026-10-07: Mayıs'tan kalan commit'lenmemiş değişiklikler (`atastudio.py`, `AtaStudio.spec`, `setup.iss`) olduğu gibi commit'lendi; içerik ayrıca gözden geçirilmedi.

- 2026-10-07: Programın amacı MP3; kayıtta MP3 dönüşümü zorunlu, TEST MODU kaldırıldı — kullanıcı kararı.

## 5. Açık sorular / bekleyenler
- LiveStreamTab'ın amacı ve tamamlanma durumu (belirsiz).
- Çalışma dizininde bozuk adlı boş dosya var: `C:UsersAtaDesktoprecordtab_dump.txt`. Silinebilir (kullanıcı onayıyla).

## 6. Araçlar ve komutlar
| Ne | Komut / yer |
|---|---|
| Çalıştır | `venv\Scripts\activate` → `python atastudio.py` |
| Bağımlılıklar | `requirements.txt` (PyQt6, yt-dlp, curl_cffi, mutagen, requests, websockets, certifi, audio-separator) |
| Exe build | `python build.py` (PyInstaller, `AtaStudio.spec`) → `dist/AtaStudio.exe` |
| Kurulum paketi | Inno Setup ile `setup.iss` derle → `installer/AtaStudio_v6.0_Setup.exe` |
| İkon | `eagle.jpg` → `eagle.ico` (build.py üretir) |
| Ayar dosyası | `.atastudio_config.json` (gitignore'da) |

## 7. Bilinen sorunlar ve tuzaklar
- `convert_log.txt` (UTF-16): WebEngine "Unable to move the cache / Gpu Cache Creation failed: Erişim engellendi (0x5)" — önbellek klasörü yazma izni sorunu.
- Yavaş modeller (htdemucs, bs_roformer) CPU'da 30-60 dk+ sürer; UI uyarı veriyor.
- `ffmpeg*.exe` kök dizinde duruyor ama repoda yok; yeni makinede ffmpeg elle kurulmalı (README de öyle diyor).
- Çalışma dizininde `build/`, `dist/`, `installer/`, `venv/` var; hepsi gitignore'da.
