# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'sqlalchemy.sql.default_comparator',
        'pymysql',
        'psycopg2',
        'pandas',
        'matplotlib',
        'cryptography'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Add icon file to the data
a.datas += [('icon.png', 'DBridge.png', 'DATA')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Set console based on platform
console = not sys.platform.startswith('win')

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='dbridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=console,  # False for Windows, True for Linux
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='DBridge.png' if sys.platform.startswith('win') else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='dbridge',
)