#!/usr/bin/env python3
"""
Ata Studio — Build Script
Çalıştır: python build.py
"""
import subprocess, sys, os, shutil
from pathlib import Path

ROOT = Path(__file__).parent

def run(cmd, **kw):
    print(f"\n▶ {' '.join(str(c) for c in cmd)}")
    subprocess.check_call(cmd, **kw)

def main():
    print("=" * 60)
    print("  Ata Studio v5.0 — Build Başlıyor")
    print("=" * 60)

    # 1. Bağımlılıkları kontrol et
    print("\n[1/5] Bağımlılıklar kontrol ediliyor...")
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])

    # 2. PyInstaller kurulu mu?
    try:
        import PyInstaller
        print(f"  ✅ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  PyInstaller bulunamadı, kuruluyor...")
        run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 3. UPX var mı? (opsiyonel, exe küçültür)
    upx = shutil.which("upx")
    if upx:
        print(f"  ✅ UPX bulundu: {upx}")
    else:
        print("  ⚠ UPX bulunamadı — exe biraz daha büyük olacak (sorun değil)")

    # 4. eagle.ico üret (eagle.jpg'den)
    print("\n[2/5] İkon üretiliyor...")
    try:
        from PIL import Image
        if Path("eagle.jpg").exists():
            img = Image.open("eagle.jpg")
            sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
            img.save("eagle.ico", format="ICO", sizes=sizes)
            print("  ✅ eagle.ico oluşturuldu")
        else:
            print("  ⚠ eagle.jpg bulunamadı, varsayılan ikon kullanılacak")
    except Exception as e:
        print(f"  ⚠ İkon üretilemedi: {e}")

    # 5. Dist klasörünü temizle
    print("\n[3/5] Eski build temizleniyor...")
    for d in ["dist", "build"]:
        if Path(d).exists():
            shutil.rmtree(d)
            print(f"  🗑 {d}/ silindi")

    # 6. PyInstaller ile derle
    print("\n[4/5] PyInstaller çalışıyor...")
    run([
        sys.executable, "-m", "PyInstaller",
        "atastudio.spec",
        "--clean",
        "--noconfirm",
    ])

    # 7. Sonuç
    exe_path = ROOT / "dist" / "AtaStudio.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / 1024 / 1024
        print("\n" + "=" * 60)
        print(f"  ✅ BAŞARILI!")
        print(f"  📦 dist/AtaStudio.exe  ({size_mb:.1f} MB)")
        print("=" * 60)
        print("\n  Kurulum için: Inno Setup ile setup.iss derle")
        print("  GitHub için:  git push origin main")
    else:
        print("\n  ❌ Build başarısız — yukarıdaki hataları kontrol et")
        sys.exit(1)

if __name__ == "__main__":
    main()