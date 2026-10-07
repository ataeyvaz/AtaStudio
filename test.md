# Ata Studio v6.0 — elle test listesi (2026-10-07)

Test edilecek build: `dist\AtaStudio.exe` (dal: `feature/transcribe`, commit `10a98ac` + sonrası).
Önceki build yedeği: `installer\AtaStudio_onceki_build.exe` (karşılaştırma için).

Her maddeyi dene, sonucu işaretle: ✅ çalıştı · ❌ hata (ne gördüğünü yaz) · ➖ denemedim.
Hata olursa **ekrandaki metni birebir** (mesaj kutusu / durum çubuğu) yaz.

## 0. Hazırlık
- [✅] Exe açılıyor mu? (ilk açılışta kurulum sihirbazı çıkarsa ayarları geç)
- [✅] Sekmeler: Dönüştür · İndir · Keşfet · Kayıt · **Yazıya Dök** · Ayarlar — hepsi görünüyor mu?
- [✅] Başlık 6.0 gösteriyor mu?
- [✅] Not: İnternet gerekir (indirme, model indirme). Test sesi: kısa bir Türkçe MP3 (1–3 dk) hazır tut.

## 1. Kayıt → MP3 (önceki düzeltme, hâlâ gerçek kayıtla denenmedi)
- [✅] Kayıt sekmesi → format **MP3** → bir şey çalıp ~15 sn kaydet → Durdur
- [✅] "MP3'e dönüştürülüyor" yazısı çıkıyor, bitince "Kaydedildi" diyalogu geliyor mu?
- [✅] Çıkan dosya **.mp3** mü (WAV değil)? Klasör: `Documents\Ata Studio\mp3`. Çalınca ses var mı?
- [ ] (İsteğe bağlı) Floating buton / tray ile kayıt başlat-durdur çalışıyor mu?
- Beklenmeyen: "WAV olarak kaydedildi (MP3 dönüştürme başarısız)" uyarısı → ffmpeg exe içinde bulunamamış demektir, yaz.

## 2. İndirme + yt-dlp (YouTube 403 düzeltmesi)
- [✅] İndir sekmesi → `https://www.youtube.com/watch?v=hUSgjqx2Uos` → MP3 → indir. 403 **çıkmamalı** (uzun video, birkaç dakika sürer).
- [✅] Bitince "İndirme Tamamlandı" diyalogunda **📝 Yazıya Dök** düğmesi görünüyor mu?
- [✅] Ayarlar → **yt-dlp Güncelleme** bölümü: "Yüklü sürüm" yazıyor mu?
- [✅] **Denetle** → "✅ Güncel" ya da "🆕 Yeni sürüm var" yazıyor mu? (hata kutusu çıkarsa metni yaz)
- [✅] (Yeni sürüm varsa) **Güncelle** → "yeniden başlatın" mesajı → uygulamayı kapat-aç → sürüm değişti mi?
- [ ] **Sıfırla** → "Sıfırlandı" mesajı çıkıyor mu? (güncelleme yapılmadıysa "Sıfırlanacak güncelleme yok" normal)

## 3. Yazıya Dök — temel akış
Küçük bir MP3 ile (1–3 dk), **Hızlı** kalitede başla.
- [ ] **Dosya Seç** ile seç → dosya adı görünüyor, "Yazıya Dök" düğmesi aktif oluyor mu?
- [ ] Başka bir dosyayı pencereye **sürükle-bırak** → seçiliyor mu? (desteklenmeyen uzantıda bırakınca kabul etmemeli)
- [ ] Dil: **Türkçe**, Kalite: **Hızlı** → ▶ Yazıya Dök
- [ ] İlk kullanımda "**Model indiriliyor, bu işlem bir kez yapılır (~145 MB)**" mesajı çıkıyor mu?
- [ ] İlerleme çubuğu ve "%NN · kalan ~MM:SS" ilerliyor, **arayüz donmuyor** mu? (pencereyi sürükle, sekme değiştir)
- [ ] Bitince "✅ Tamamlandı"; metin Türkçe karakterlerle doğru okunuyor mu?
- [ ] Metin paragraflara bölünmüş mü (uzun sessizliklerde yeni paragraf)?
- [ ] **Zaman damgası** kutusunu işaretle → her paragrafın başında `[00:00:00]` çıkıyor, kaldırınca gidiyor mu?
- [ ] Metni elle düzenle, sonra zaman damgası kutusunu aç/kapat → düzenlediğin metin **silinmiyor**, durum çubuğunda uyarı çıkıyor mu?
- [ ] Çalışırken bilgisayar belirgin kasılıyor mu? (düşük öncelik denendi; yavaşlık varsa yaz)

## 4. Yazıya Dök — iptal
- [ ] Daha uzun bir dosyayla başlat, birkaç paragraf oluşunca **⏹ İptal**
- [ ] "İptal edildi — metin korundu" yazıyor, o ana kadarki metin duruyor mu?
- [ ] İptalden hemen sonra yeniden başlatabiliyor musun?
- [ ] Görev Yöneticisi'nde işlem bitince fazladan `AtaStudio.exe` süreci **kalmamış** olmalı (kontrol et)

## 5. Yazıya Dök — kalite / dil
- [ ] **Dengeli** (small, ~480 MB) ile aynı dosya → sonuç Hızlı'dan daha doğru mu? Süre ne kadar? (not al)
- [ ] **English** dil seçip İngilizce bir ses dene
- [ ] **Otomatik algıla** ile bir ses dene → durum çubuğunda algılanan dil yazıyor mu?
- [ ] (İsteğe bağlı, uzun sürer + ~1,5 GB indirir) **Hassas**
- [ ] **İnternetsiz hata:** henüz inmemiş bir model seç (ör. Hassas), interneti kes → ▶ → "Model indirilemedi, internet bağlantınızı kontrol edin" kutusu çıkıyor mu? (interneti geri aç)

## 6. Kaydet / kopyala / aç
- [✅] **Panoya kopyala** → Not Defteri'ne yapıştır → doğru mu?
- [ ] **.txt kaydet** → dosya `Documents\Ata Studio\metin` önerilen klasörde, Türkçe karakterler bozuk değil mi?
- [ ] **.docx kaydet** → Word'de açılıyor, paragraflar doğru mu?
- [ ] **.srt kaydet** → bir video oynatıcıda (ör. VLC) ses dosyasıyla altyazı olarak çalışıyor mu?
- [ ] **Şununla aç ▾ → Not Defteri** → metin Not Defteri'nde açılıyor mu?
- [ ] **Şununla aç ▾ → Word** → .docx varsayılan programda açılıyor mu?

## 7. Sözcük bağlantısı
- [ ] Ayarlar → **Sözcük Bağlantısı** → başlatıcıyı seç (Sözcük.bat / main.py / exe) → Kaydet
- [ ] main.py seçtiysen **Python** alanına python.exe / pythonw.exe yolunu da ver (boş bırakırsan PATH'te python gerekir)
- [ ] Yazıya Dök → **Şununla aç ▾ → Sözcük** → Sözcük açılıyor ve metin dosyasını yüklüyor mu?
- [ ] Yol hiç ayarlanmamışken aynı menüyü dene → "yol seçilmemiş" kutusu çıkıp dosya seçtiriyor mu?

## 8. İndir → Yazıya Dök köprüsü
- [ ] Kısa bir video/ses indir → diyalogda **📝 Yazıya Dök** → Yazıya Dök sekmesine geçip dosya seçili geliyor mu?
- [ ] ▶ ile başlatınca çalışıyor mu?

## 9. Eski düzeltme: yavaş model uyarısı
- [ ] Dönüştür sekmesi → ses ayırma modeli olarak **htdemucs** ya da **bs_roformer** seç → uygulama **çökmeden** "Yavaş Model Uyarısı" kutusu çıkıyor mu?
- [ ] Hayır dersen MDX-NET'e geri dönüyor mu?

## 10. Genel gözlemler
- Exe boyutu (dist\AtaStudio.exe): ______ MB (önceki: 923 MB)
- Açılış süresi: ______ sn
- Yazıya Dök, 3 dk'lık ses için Hızlı / Dengeli süreleri: ______ / ______
- Diğer notlar, garip davranışlar:

## Sonuç bildirimi
Bitince şunu yaz: "Test bitti: şu maddeler ❌ → <madde no + ekrandaki metin>". Hepsi ✅ ise "Hepsi tamam, main'e birleştir" de.
Bir sonraki aşama: Whisper'lı yazıya dökme özelliğini **Sözcük** projesine eklemek.
