# -*- mode: python ; coding: utf-8 -*-

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
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add icon file to the data
a.datas += [('icon.png', 'DBridge.png', 'DATA')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for GUI application
    disable_windowed_traceback=False,
    argv_emulation=True,  # Enable argv emulation for macOS
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='DBridge.icns',  # Use the ICNS icon for macOS
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DBridge',
)

# Create macOS application bundle
app = BUNDLE(
    coll,
    name='DBridge.app',
    icon='DBridge.icns',
    bundle_identifier='com.dbridge.app',
    info_plist={
        'CFBundleShortVersionString': '0.8.0',
        'CFBundleVersion': '0.8.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,  # Allow dark mode
        'CFBundleDisplayName': 'DBridge',
        'CFBundleName': 'DBridge',
        'CFBundleExecutable': 'DBridge',
        'CFBundleIdentifier': 'com.dbridge.app',
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundlePackageType': 'APPL',
        'LSApplicationCategoryType': 'public.app-category.developer-tools',
        'LSMinimumSystemVersion': '10.14.0',  # Minimum macOS version
    },
)