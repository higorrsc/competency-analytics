#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    """Run administrative tasks."""
    script_dir = str(Path(__file__).resolve().parent)
    project_root = str(Path(__file__).resolve().parent.parent.parent)

    # Avoid script directory shadowing the top-level 'django' package
    if sys.path and sys.path[0] == script_dir:
        sys.path.pop(0)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "src.infrastructure.config.settings",
    )
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
