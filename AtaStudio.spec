# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
curl_datas = collect_data_files('curl_cffi')

a = Analysis(
    ['atastudio.py'],
    pathex=[],
    binaries=[],
    datas=curl_datas,
    hiddenimports=[
        'PyQt6.QtCore','PyQt6.QtGui','PyQt6.QtWidgets','PyQt6.QtNetwork',
        'yt_dlp','yt_dlp.extractor','yt_dlp.networking._curlcffi',
        'yt_dlp.networking._requests','curl_cffi','curl_cffi.requests',
        'mutagen','certifi','websockets','requests','urllib3',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter','tensorflow','tensorflow_intel','keras',
        'torch','torchvision','torchaudio',
        'numpy','pandas','scipy','sklearn',
        'matplotlib','cv2','onnxruntime','ml_dtypes',
        'audio_separator','demucs','librosa','soundfile',
        'numba','llvmlite','sympy','IPython','jupyter',
        'test','unittest','pytest','mp3tomid',
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='AtaStudio',
    debug=False, strip=False, upx=True,
    console=False, upx_exclude=[],
    icon='eagle.ico',
    version='version_info.txt',
)
