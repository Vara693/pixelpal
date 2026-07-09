# PyInstaller spec — macOS
#
# Build from the repo root with:
#   pyinstaller packaging/pyinstaller/macos.spec
#
# Produces dist/PixelPal.app. LSUIElement is set so the app runs as a
# background/agent app with no Dock icon or menu bar, appropriate for
# an always-on-top desktop pet.

# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPEC), "..", ".."))

a = Analysis(
    [os.path.join(REPO_ROOT, "pixelpal", "main.py")],
    pathex=[REPO_ROOT],
    binaries=[],
    datas=[
        (os.path.join(REPO_ROOT, "chars"), "chars"),
    ],
    hiddenimports=[
        "PySide6.QtSvg",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PixelPal",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PixelPal",
)

app = BUNDLE(
    coll,
    name="PixelPal.app",
    icon=None,  # point at an .icns once branded art exists
    bundle_identifier="com.pixelpal.desktoppet",
    info_plist={
        "LSUIElement": True,  # no Dock icon / menu bar — background agent app
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
    },
)
