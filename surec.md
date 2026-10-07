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

Son commit: `main` üzerinde (push edilmedi: GitHub'da son `83fd0ac`) · Testler: yok (otomatik test dosyası bulunmuyor).

## 2. Sıradaki işler (öncelik sırasıyla)
0. ~~Whisper → Sözcük~~ — **yapıldı** (Sözcük 1.4, `C:\Users\Ata\Desktop\sozcuk`, dal `ozellik/dosyadan-yazi`, push edilmedi). Ata Studio'da Whisper YOK. Arşiv: `whisper-arsiv` etiketi. Sözcük'te ses çözücü soundfile: mp3/wav/opus/ogg/flac (mp4/m4a desteklenmez; PyAV'ın FFmpeg'i GPL'li olduğu için kullanılmadı). Ayrıntı: Sözcük `surec.md` (7 Ekim 2026).
0b. **Paketler hazır (2026-10-07):** `dist\AtaStudio.exe` (929 MB, Whisper'sız `main`, açılışı doğrulandı) ve `installer\AtaStudio_v6.0_Setup.exe` (1039 MB). Eski paket: `installer\AtaStudio_v6.0_Setup_onceki.exe`. Sürüm numarası 6.0 kaldı (Mayıs'taki 6.0 paketinden farklı içerik — istenirse 6.1'e çıkarılır). Kurulum paketi yalnızca derlendi, **kurulup denenmedi**.
0c. **Uyarı (lisans):** `setup.iss` `ffmpeg.exe/ffprobe.exe/ffplay.exe`'yi kurulum paketine koyuyor; bu derlemeler büyük olasılıkla GPL'li. Kişisel kullanım için sorun değil; geniş dağıtımda kontrol edilmeli (LGPL derleme ya da kullanıcının kendi kurması).
1. ~~Kayıt MP3~~ — kullanıcı exe'de denedi ✅ (2026-10-07).
2. ~~ffmpeg yolu~~ — sabit yol kaldırıldı, `_find_ffmpeg()` (exe içi → uygulama klasörü → PATH).
3. ~~Sürüm tutarsızlığı~~ — başlık, `build.py`, README 6.0'a çekildi.
4. ~~README~~ — kayıt ve yt-dlp güncelleme eklendi; gömülü browser/floating buton ayrıntısı eksik kalabilir.
4b. ~~Exe yeniden build~~ — yapıldı (bkz. 0b). venv'de faster-whisper/python-docx kurulu kalıyor (zararsız, pakete girmedi; istenirse `pip uninstall faster-whisper python-docx`). Önceki (Whisper'lı dal) build: `installer\AtaStudio_onceki_build.exe` değil, o Mayıs'taki build; Whisper'lı build ezildi (kaynak `whisper-arsiv` etiketinden yeniden üretilebilir).
4c. Diğer platformlarda (YouTube dışı) indirme denenmedi.
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

- 2026-10-07: YouTube 403 hatası → sebep eski yt-dlp (2026.03.17). venv ve requirements.txt 2026.8.19'a çekildi; uygulamanın akışıyla uzun podcast videosu MP3'e indirildi. Exe'nin içindeki yt-dlp eski kalır, yeniden build gerekir.

- 2026-10-07: Ayarlar'a yt-dlp güncelleme eklendi (Denetle/Güncelle/Sıfırla). Exe'de güncelleme `%APPDATA%\AtaStudio\ytdlp` içine açılır ve gömülü sürümden yeniyse açılışta öne alınır (mini PyInstaller denemesiyle doğrulandı). Kaynaktan çalışırken `pip install -U` kullanılır.
- 2026-10-07: Whisper (yazıya dök) Ata Studio'ya EKLENMEYECEK — uygulamayı şişirir (+~130 MB, ayrıca ctranslate2/av). Kullanıcı Ata Studio'da çalıştığını gördü (test başarılı), sonra Sözcük projesine taşımaya karar verdi. Çalışma `feature/transcribe` dalında ve `whisper-arsiv` etiketinde saklı (main'e birleştirilmedi). Geri dönüş noktası: `v6.0-oncesi-whisper`.
- 2026-10-07: Kullanıcı testi (exe): açılış, sekmeler, kayıt→MP3, YouTube MP3 indirme (403 yok), yt-dlp Denetle/Güncelle, Whisper yazıya dök ✅. Diğer platformlar denenmedi.
- 2026-10-07: PyQt6'da kısa enum adları (`QMessageBox.Yes`) çalışmaz → `QMessageBox.StandardButton.Yes` kullan (yavaş model uyarısı bu yüzden çöküyordu, düzeltildi).

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
- YouTube indirmeleri yt-dlp eskidikçe 403 verir; sık güncelle (`pip install -U yt-dlp`) ve exe'yi yeniden build et. yt-dlp ayrıca JS runtime (deno) önerir; şu an uyarı veriyor ama indirme çalışıyor.
- `convert_log.txt` (UTF-16): WebEngine "Unable to move the cache / Gpu Cache Creation failed: Erişim engellendi (0x5)" — önbellek klasörü yazma izni sorunu.
- Yavaş modeller (htdemucs, bs_roformer) CPU'da 30-60 dk+ sürer; UI uyarı veriyor.
- `ffmpeg*.exe` kök dizinde duruyor ama repoda yok; yeni makinede ffmpeg elle kurulmalı (README de öyle diyor).
- Çalışma dizininde `build/`, `dist/`, `installer/`, `venv/` var; hepsi gitignore'da.
