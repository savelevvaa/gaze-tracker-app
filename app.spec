# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/trackerApp/venv/Lib/site-packages/mediapipe/modules/face_landmark/face_landmark_front_cpu.binarypb', 'mediapipe/modules/face_landmark'), ('C:/trackerApp/venv/Lib/site-packages/mediapipe/modules/face_landmark/face_landmark_with_attention.tflite', 'mediapipe/modules/face_landmark'), ('C:/trackerApp/venv/Lib/site-packages/mediapipe/modules/face_detection/face_detection_short_range.tflite', 'mediapipe/modules/face_detection')],
    hiddenimports=['mediapipe', 'mediapipe.python.solutions.face_mesh'],
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
    name='app',
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
    icon=['C:\\trackerApp\\icon.ico'],
)
