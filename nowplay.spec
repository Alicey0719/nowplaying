from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [*collect_data_files("customtkinter"), ("icon_source.png", ".")]

hiddenimports = [
    *collect_submodules("winrt"),
    "win32clipboard",
    "pywintypes",
]

a = Analysis(
    ["nowplay.pyw"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="NowPlaying",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon="_icon.ico",
)
