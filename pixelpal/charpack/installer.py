"""Install a new char pack from a .zip file into the user's chars directory.

The zip is expected to contain a single top-level folder (or its
contents directly) with a config.json at its root, matching the
structure documented in docs/CHARS.md.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import zipfile

from pixelpal.charpack.loader import CharPackLoadError, load_char_pack

MAX_ZIP_UNCOMPRESSED_BYTES = 200 * 1024 * 1024  # 200 MB safety cap


class CharPackInstallError(ValueError):
    pass


def _safe_extract(zf: zipfile.ZipFile, dest: str) -> None:
    """Extract a zip while guarding against path traversal / zip bombs."""
    total_size = 0
    for info in zf.infolist():
        total_size += info.file_size
        if total_size > MAX_ZIP_UNCOMPRESSED_BYTES:
            raise CharPackInstallError("Char pack zip is too large; refusing to install.")

        member_path = os.path.normpath(os.path.join(dest, info.filename))
        if not member_path.startswith(os.path.normpath(dest) + os.sep) and member_path != dest:
            raise CharPackInstallError(
                f"Zip contains an unsafe path outside the extraction target: {info.filename}"
            )

    zf.extractall(dest)


def _find_config_root(extracted_dir: str) -> str:
    """Locate the folder within extracted_dir that actually has config.json.

    Handles both "zip contains files at root" and "zip contains one
    wrapper folder" layouts.
    """
    if os.path.isfile(os.path.join(extracted_dir, "config.json")):
        return extracted_dir

    entries = [
        e for e in os.listdir(extracted_dir)
        if os.path.isdir(os.path.join(extracted_dir, e))
    ]
    if len(entries) == 1:
        candidate = os.path.join(extracted_dir, entries[0])
        if os.path.isfile(os.path.join(candidate, "config.json")):
            return candidate

    raise CharPackInstallError(
        "Could not find config.json at the root of the zip (or its single wrapper folder)."
    )


def install_char_pack_from_zip(zip_path: str, chars_dir: str) -> str:
    """Install a char pack zip into chars_dir. Returns the installed pack's name.

    Validates the pack (via charpack.loader) *before* moving it into
    place, so a broken zip never corrupts an existing install.
    """
    if not os.path.isfile(zip_path):
        raise CharPackInstallError(f"Zip file not found: {zip_path}")

    with tempfile.TemporaryDirectory(prefix="pixelpal_charpack_") as tmp:
        try:
            with zipfile.ZipFile(zip_path) as zf:
                _safe_extract(zf, tmp)
        except zipfile.BadZipFile as exc:
            raise CharPackInstallError(f"Not a valid zip file: {exc}") from exc

        config_root = _find_config_root(tmp)

        try:
            pack = load_char_pack(config_root)
        except CharPackLoadError as exc:
            raise CharPackInstallError(f"Char pack failed validation: {exc}") from exc

        target_dir = os.path.join(chars_dir, pack.config.name)
        if os.path.exists(target_dir):
            raise CharPackInstallError(
                f"A char pack named '{pack.config.name}' is already installed."
            )

        os.makedirs(chars_dir, exist_ok=True)
        shutil.copytree(config_root, target_dir)

        return pack.config.name


def uninstall_char_pack(name: str, chars_dir: str) -> None:
    target_dir = os.path.join(chars_dir, name)
    if not os.path.isdir(target_dir):
        raise CharPackInstallError(f"No installed char pack named '{name}'.")
    shutil.rmtree(target_dir)
