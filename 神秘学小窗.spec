# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['show.py'],
    pathex=[],
    binaries=[],
    datas=[('ArcanistsHuman', 'ArcanistsHuman'), ('songs', 'songs'), ('operate_intro.txt', '.'), ('update_log.txt', '.')],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='神秘学小窗',
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
    icon=['ArcanistsHuman/component_pic/icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='神秘学小窗',
)
