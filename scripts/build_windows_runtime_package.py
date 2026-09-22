from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "deliverables"
RELEASE_NAME = "borna-chart-windows-selfcontained-iis-kit-20260922"
RELEASE_DIR = OUT_DIR / RELEASE_NAME
ZIP_PATH = OUT_DIR / f"{RELEASE_NAME}.zip"

INCLUDE_FILES = [
    ".env.example",
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "OPEN_ME_FIRST.bat",
    "RESET_AND_RUN_DEMO.bat",
    "RUN_ON_SERVER_IP.bat",
    "ENABLE_WINDOWS_FIREWALL_8000.bat",
    "OPEN_IIS_DEPLOY_GUIDE.bat",
    "INSTALL_PYTHON_FIRST.bat",
    "run_borna_server.bat",
    "run_borna_server_reset_demo.bat",
    "setup_windows_env.bat",
]

INCLUDE_DIRS = [
    "app",
    "config",
    "deploy",
    "docs",
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
    return (
        any(part in EXCLUDE_DIRS for part in path.parts)
        or path.name in EXCLUDE_NAMES
        or path.suffix in EXCLUDE_SUFFIXES
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())


def reset_release_dir() -> None:
    if RELEASE_DIR.exists():
        for p in sorted(RELEASE_DIR.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            else:
                p.rmdir()
        RELEASE_DIR.rmdir()
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)


def build_release_tree() -> None:
    reset_release_dir()

    for rel in INCLUDE_FILES:
        src = ROOT / rel
        if src.exists():
            copy_file(src, RELEASE_DIR / rel)

    for rel in INCLUDE_DIRS:
        src_dir = ROOT / rel
        if not src_dir.exists():
            continue
        for src in src_dir.rglob("*"):
            rel_path = src.relative_to(ROOT)
            if src.is_dir() or should_skip(rel_path):
                continue
            copy_file(src, RELEASE_DIR / rel_path)

    write_text(
        RELEASE_DIR / "START_HERE_FA.txt",
        """BORNA WINDOWS SELF-CONTAINED IIS KIT

1) Python 3.11 or newer must be installed.
2) For local quick start: double-click OPEN_ME_FIRST.bat
3) For LAN access: run ENABLE_WINDOWS_FIREWALL_8000.bat and then RUN_ON_SERVER_IP.bat
4) For a fresh demo database each time: run RESET_AND_RUN_DEMO.bat
5) If Python is not installed yet: run INSTALL_PYTHON_FIRST.bat
6) For IIS / Reverse Proxy deployment: run OPEN_IIS_DEPLOY_GUIDE.bat

Main guides:
- docs/windows_run_guide_fa.md
- docs/windows_server_deploy_iis_fa.md
""",
    )

    write_text(
        RELEASE_DIR / "docs" / "release_package_notes_fa.md",
        """# بسته Windows Self-Contained + IIS Kit

این بسته برای اجرای سریع، یک‌کلیکی، و همچنین استقرار رسمی‌تر روی Windows Server آماده شده است.

## فایل‌هایی که کاربر نهایی باید ببیند
- OPEN_ME_FIRST.bat
- RUN_ON_SERVER_IP.bat
- RESET_AND_RUN_DEMO.bat
- ENABLE_WINDOWS_FIREWALL_8000.bat
- OPEN_IIS_DEPLOY_GUIDE.bat

## شامل چه چیزهایی است؟
- API FastAPI
- Web Console
- فایل‌های BAT برای setup و run
- نمونه Firewall helper
- راهنمای IIS / Reverse Proxy
- تنظیمات workflow/config

## عمداً در این بسته نیامده است
- tests
- prototype
- virtual environment محلی
- artifacts توسعه
""",
    )


def build_zip() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with ZipFile(ZIP_PATH, "w", compression=ZIP_DEFLATED) as zf:
        for src in sorted(RELEASE_DIR.rglob("*")):
            if src.is_dir():
                continue
            zf.write(src, arcname=f"{RELEASE_NAME}/{src.relative_to(RELEASE_DIR)}")


if __name__ == "__main__":
    build_release_tree()
    build_zip()
    print(ZIP_PATH)
