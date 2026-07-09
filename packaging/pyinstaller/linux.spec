# PyInstaller spec — Linux
#
# Build from the repo root with:
#   pyinstaller packaging/pyinstaller/linux.spec
#
# Output: dist/pixelpal/pixelpal (onedir build; simplest to debug
# missing-data-file issues with bundled char pack assets).

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
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pixelpal",
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
    name="pixelpal",
)
