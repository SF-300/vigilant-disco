#! /usr/bin/env -S uv run

"""Task automation for Anki addon development using doit."""

import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Dict, Any

# Constants
ANKI_ADDONS_DIR = Path.home() / ".local" / "share" / "Anki2" / "addons21"
ADDON_NAME = "my-anki-addon"
PYTHON_PATHS = ["src", "tests"]


def task_test() -> Dict[str, Any]:
    """Run tests with pytest and coverage."""
    return {
        "actions": ["uv run pytest"],
        "verbosity": 2,
    }


def task_type_check() -> Dict[str, Any]:
    """Run static type checking with mypy."""
    return {"actions": [f"mypy {path}" for path in PYTHON_PATHS]}


def task_format() -> Dict[str, Any]:
    """Format code with black and isort."""
    return {
        "actions": [
            f"black {' '.join(PYTHON_PATHS)}",
            f"isort {' '.join(PYTHON_PATHS)}",
        ]
    }


def task_lint() -> Dict[str, Any]:
    """Run all linting tasks."""
    return {"actions": None, "task_dep": ["type_check", "format"]}


def task_package() -> Dict[str, Any]:
    """Create .ankiaddon file.
    
    Following Anki add-on packaging requirements:
    - Includes all files from src/ directory (recursively)
    - Includes manifest.json from root
    - Excludes __pycache__ directories
    - Creates a flat structure in the ZIP as required by Anki
    """

    def create_addon() -> None:
        """Package the addon sources into a ZIP file."""
        addon_file = Path(f"{ADDON_NAME}.ankiaddon")
        if addon_file.exists():
            addon_file.unlink()

        with zipfile.ZipFile(addon_file, "w") as zf:
            # Add manifest.json from root
            manifest = Path("manifest.json")
            if manifest.exists():
                zf.write(manifest, arcname=manifest.name)

            # Add all files from src/ recursively
            src_path = Path("src")
            for file in src_path.rglob("*"):
                # Skip __pycache__ directories and their contents
                if "__pycache__" in file.parts:
                    continue
                # Skip .egg-info directories
                if ".egg-info" in file.parts:
                    continue
                # Only package files, not directories
                if file.is_file():
                    # Remove src/ prefix to create flat structure
                    rel_path = file.relative_to(src_path)
                    zf.write(file, arcname=str(rel_path))

    return {
        "actions": [(create_addon,)],
        "targets": [f"{ADDON_NAME}.ankiaddon"],
        "task_dep": ["test", "lint"],  # Ensure quality before packaging
    }


def task_dev_install() -> Dict[str, Any]:
    """Install addon to local Anki for development."""
    target_dir = ANKI_ADDONS_DIR / ADDON_NAME

    def install_addon() -> None:
        """Install the addon to Anki addons directory."""
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(f"{ADDON_NAME}.ankiaddon") as zf:
            zf.extractall(target_dir)

    return {"actions": [(install_addon,)], "task_dep": ["package"]}


# def task_clean() -> Dict[str, Any]:
#     """Clean build artifacts."""
#     patterns = [
#         "build/",
#         "dist/",
#         "*.egg-info",
#         ".pytest_cache",
#         ".mypy_cache",
#         ".coverage",
#         "**/__pycache__",
#         f"{ADDON_NAME}.ankiaddon",
#     ]

#     def clean_paths() -> None:
#         """Remove build artifacts and caches."""
#         for pattern in patterns:
#             for path in Path().glob(pattern):
#                 if path.is_dir():
#                     shutil.rmtree(path)
#                 else:
#                     path.unlink()

#     return {"actions": [(clean_paths,)]}


if __name__ == "__main__":
    import doit

    # NOTE: Hide "warning: `VIRTUAL_ENV=...` does not match the project environment path `.venv` and will be ignored"
    #       * https://github.com/astral-sh/uv/issues/7073#issuecomment-2567677362
    # del os.environ["VIRTUAL_ENV"]

    doit.run(globals())
