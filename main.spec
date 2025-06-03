# -*- mode: python ; coding: utf-8 -*-

import warnings
warnings.filterwarnings('ignore')

from PyInstaller.utils.hooks import collect_all  
 
# 一次性获取 flask-orm 的所有资源  
flask_datas, flask_binaries, flask_hiddenimports = collect_all('flask_socketio')  


a = Analysis(
    ['backend\\main.py'],
    pathex=[],
    binaries=flask_binaries,
    datas=[*flask_datas],
    hiddenimports=flask_hiddenimports,
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
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='main',
)
