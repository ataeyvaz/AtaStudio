# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files

# faster-whisper / ctranslate2 için hazır PyInstaller kancası yok:
#  - ctranslate2: DLL'ler ve veri dosyaları
#  - faster_whisper: assets/silero_vad_v6.onnx (VAD filtresi)
_ct2_datas, _ct2_bins, _ct2_hidden = collect_all('ctranslate2')
_fw_datas = collect_data_files('faster_whisper')

a = Analysis(
    ['atastudio.py'],
    pathex=[],
    binaries=[('ffmpeg.exe', '.'), ('ffprobe.exe', '.'), ('ffplay.exe', '.')] + _ct2_bins,
    datas=_ct2_datas + _fw_datas,
    hiddenimports=['PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore', 'pyaudiowpatch', 'basic_pitch', 'onnxruntime',
                   'transcribe_engine', 'faster_whisper', 'docx'] + _ct2_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AtaStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['eagle.ico'],
)
