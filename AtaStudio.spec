# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['atastudio.py'],
    pathex=[],
    binaries=[('ffmpeg.exe', '.'), ('ffprobe.exe', '.'), ('ffplay.exe', '.')],
    datas=[],
    hiddenimports=['PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore', 'pyaudiowpatch', 'basic_pitch', 'onnxruntime'],
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
