from __future__ import annotations

import shutil
import subprocess
import tarfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "deliverables"
RELEASE_NAME = "borna-chart-windows-truly-portable-20260922"
RELEASE_DIR = OUT_DIR / RELEASE_NAME
ZIP_PATH = OUT_DIR / f"{RELEASE_NAME}.zip"
BUILD_DIR = OUT_DIR / ".build-truly-portable"
PYTHON_EMBED_VERSION = "3.12.0"
RUNTIME_REQS = ROOT / "portable" / "requirements_runtime_windows_cp312.txt"

INCLUDE_FILES = [
    ".env.example",
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "PORTABLE_OPEN_ME_FIRST.bat",
    "PORTABLE_RUN_ON_SERVER_IP.bat",
    "PORTABLE_RESET_AND_RUN_DEMO.bat",
    "ENABLE_WINDOWS_FIREWALL_8000.bat",
    "OPEN_IIS_DEPLOY_GUIDE.bat",
]

INCLUDE_DIRS = [
    "app",
    "config",
    "deploy",
    "docs",
    "portable",
]

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "build",
    "dist",
    "coverage",
    "target",
    "deliverables",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".db"}
EXCLUDE_NAMES = {"borna_chart.db"}


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts) or path.name in EXCLUDE_NAMES or path.suffix in EXCLUDE_SUFFIXES


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, cwd=ROOT)


def prepare_release_tree() -> None:
    reset_dir(RELEASE_DIR)
    for rel in INCLUDE_FILES:
        src = ROOT / rel
        if src.exists():
            copy_file(src, RELEASE_DIR / rel)
    for rel in INCLUDE_DIRS:
        src_dir = ROOT / rel
        if not src_dir.exists():
            continue
        for src in src_dir.rglob('*'):
            rel_path = src.relative_to(ROOT)
            if src.is_dir() or should_skip(rel_path):
                continue
            copy_file(src, RELEASE_DIR / rel_path)


def download_python_embed() -> Path:
    reset_dir(BUILD_DIR)
    run([
        "python", "-m", "pip", "download",
        "--dest", str(BUILD_DIR),
        f"python-embed=={PYTHON_EMBED_VERSION}",
    ])
    candidates = sorted(BUILD_DIR.glob("python_embed-*.tar.gz"))
    if not candidates:
        raise RuntimeError("python-embed source package was not downloaded")
    return candidates[0]


def extract_embed_payload(embed_tgz: Path, dest_zip: Path) -> None:
    with tarfile.open(embed_tgz, "r:gz") as tf:
        member = next((m for m in tf.getmembers() if m.name.endswith("data.zip")), None)
        if member is None:
            raise RuntimeError("python-embed package did not contain data.zip")
        fileobj = tf.extractfile(member)
        if fileobj is None:
            raise RuntimeError("python-embed data.zip could not be extracted")
        dest_zip.parent.mkdir(parents=True, exist_ok=True)
        dest_zip.write_bytes(fileobj.read())


def download_wheelhouse(dest_dir: Path) -> None:
    reset_dir(dest_dir)
    run([
        "python", "-m", "pip", "download",
        "--dest", str(dest_dir),
        "--only-binary=:all:",
        "--platform", "win_amd64",
        "--python-version", "312",
        "--implementation", "cp",
        "-r", str(RUNTIME_REQS),
    ])


def write_start_here() -> None:
    text = """BORNA WINDOWS TRULY PORTABLE PACKAGE

1) Double-click PORTABLE_OPEN_ME_FIRST.bat
2) For LAN access: run ENABLE_WINDOWS_FIREWALL_8000.bat and then PORTABLE_RUN_ON_SERVER_IP.bat
3) For a fresh demo database each time: run PORTABLE_RESET_AND_RUN_DEMO.bat
4) For IIS / Reverse Proxy deployment: run OPEN_IIS_DEPLOY_GUIDE.bat

This package carries its own embedded Python runtime payload and offline wheelhouse for runtime dependencies.
"""
    (RELEASE_DIR / "START_HERE_PORTABLE_FA.txt").write_text(text, encoding="utf-8")


def build_zip() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with ZipFile(ZIP_PATH, "w", compression=ZIP_DEFLATED) as zf:
        for src in sorted(RELEASE_DIR.rglob('*')):
            if src.is_dir():
                continue
            zf.write(src, arcname=f"{RELEASE_NAME}/{src.relative_to(RELEASE_DIR)}")


if __name__ == "__main__":
    prepare_release_tree()
    embed_tgz = download_python_embed()
    extract_embed_payload(embed_tgz, RELEASE_DIR / "portable_assets" / "python-embed-cp312.zip")
    download_wheelhouse(RELEASE_DIR / "portable_assets" / "wheelhouse")
    write_start_here()
    build_zip()
    print(ZIP_PATH)
