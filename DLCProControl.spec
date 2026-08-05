# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('auto_lock_algorithm_presets.json', '.'),
        ('tools/program_fpga_bit.tcl', 'tools'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # This workstation uses a broad Anaconda environment that also contains
    # PyQt5 and many notebook/documentation tools.  The application is
    # exclusively PySide6; excluding unrelated development stacks prevents
    # PyInstaller from collecting a second Qt binding and keeps the operator
    # package deterministic and compact.
    excludes=[
        'PyQt5',
        'PyQt6',
        'IPython',
        'pytest',
        'sphinx',
        'docutils',
        'matplotlib',
        'black',
        'astroid',
        'jedi',
        'nbformat',
        'notebook',
        'tkinter',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DLCProControl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DLCProControl',
)
