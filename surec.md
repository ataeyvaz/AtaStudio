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
| Yazıya Dök (TranscribeTab) | faster-whisper ile çevrimdışı ses→metin | `transcribe_engine.py` + sekme; kaynaktan test edildi (40 sn Türkçe örnek, iptal, txt/docx/srt, Sözcük .bat) | 🟡 exe'de denenmedi |
| Canlı yayın (LiveStreamTab) | | Kodda var; kapsamı belirsiz | ❓ |
| Kurulum paketi | Inno Setup ile Setup.exe | `setup.iss` v6.0, `installer/` içinde v5.0 ve v6.0 Setup.exe mevcut | ✅ |

Son commit: `2a12a0a` (2026-10-07, push edildi) · Testler: yok (otomatik test dosyası bulunmuyor).

## 2. Sıradaki işler (öncelik sırasıyla)
0. **Whisper "Yazıya Dök" — kullanıcı testi bekleniyor** (`feature/transcribe` dalı, henüz main'e birleşmedi). Kod hazır ve kaynaktan test edildi; **tam exe build'i yapılmadı**; küçük deneme exe'siyle (konsolsuz, onefile) kendi kendini işçi olarak başlatma + VAD + ctranslate2 doğrulandı. Elle denenecekler: (a) `python build.py` ile build; (b) exe'de Yazıya Dök — model indirme mesajı, ilerleme/ETA, iptal; (c) İndir → bitince "Yazıya Dök" düğmesi; (d) Ayarlar > Sözcük yolu → "Şununla aç > Sözcük"; (e) .docx'i Word'de aç; (f) Ayarlar > yt-dlp Denetle/Güncelle.
0b. ~~PyQt6 enum hatası~~ — doğrulandı ve düzeltildi: yavaş-model uyarısı (`htdemucs`/`bs_roformer` seçimi) `QMessageBox.Yes` yüzünden AttributeError ile çöküyordu; `StandardButton.Yes/No` yapıldı. Elle de dene.
1. **Kayıt MP3 dönüşümünü gerçek kayıtla dene** (2026-10-07'de geri açıldı: `_find_ffmpeg()` ile ffmpeg bulunuyor, başarısızsa WAV'a düşüp uyarı veriyor; debug print'ler silindi). Paketli exe'de ffmpeg'in bulunduğunu da doğrula.
2. ~~ffmpeg yolu~~ — sabit yol kaldırıldı, `_find_ffmpeg()` (exe içi → uygulama klasörü → PATH).
3. ~~Sürüm tutarsızlığı~~ — dosya başlığı, `build.py`, README 6.0'a çekildi (feature/transcribe dalında).
4. ~~README~~ — kayıt, Yazıya Dök, yt-dlp güncelleme eklendi; gömülü browser/floating buton ayrıntısı eksik kalabilir.
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
- 2026-10-07: Whisper (yazıya dök) `feature/transcribe` dalında geliştirilecek; main'e birleştirmeden önce kullanıcı onayı şart. Geri dönüş noktası: `v6.0-oncesi-whisper` etiketi.

- 2026-10-07: Yazıya Dök mimarisi: ağır iş AYRI SÜREÇTE (`atastudio.py --transcribe-worker ...`, exe'de kendi kendini başlatır), düşük öncelik (BELOW_NORMAL), çıktı stdout'ta JSON satırları. Neden: thread önceliği CTranslate2'nin kendi iş parçacıklarını etkilemez, iptal temiz olur, multiprocessing/freeze_support gerekmez.
- 2026-10-07: İptal kanalı stdin DEĞİL, bayrak dosyası + ana süreç kontrolü. Neden: iş parçacığında `os.read(0)` ile bloke olmak `faster_whisper` import'unu sessizce (çıkış kodu 1) çökertti. Çözüm testle doğrulandı.
- 2026-10-07: Kalite = Hızlı/Dengeli/Hassas → base/small/medium (beam 1/3/3), dil varsayılan Türkçe, VAD açık, int8, `condition_on_previous_text=False`. Çıktı: txt/docx + ek olarak srt. Metin klasörü: `Documents\Ata Studio\metin`.
- 2026-10-07: Sözcük yolu ve (yalnızca .py için) Python yolu config'e kaydedilir (`sozcuk_path`, `sozcuk_python`); kişisel yol gömülü değil; exe'de `sys.executable` ASLA Python yerine kullanılmaz.

## 5. Açık sorular / bekleyenler
- Exe boyutu: mevcut exe 923 MB; `ctranslate2` (~60 MB) + `av` (~65 MB) eklenir (~+130 MB). Build sonrası `dist/AtaStudio.exe` boyutuna bak.
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
