#!/usr/bin/env python3
"""
Setup helper that discovers KiCad's Python and configures the environment.
"""

import subprocess
import sys
from pathlib import Path


def get_kicad_python_path():
    """Use kigadgets to discover KiCad's Python interpreter path."""
    try:
        from kigadgets.environment import get_default_paths
        paths = get_default_paths()
        kipython_paths = paths.get('kipython', [])
        if kipython_paths:
            return kipython_paths[0]
    except Exception as e:
        print(f"Error discovering KiCad Python: {e}", file=sys.stderr)
    return None


def main():
    """Setup the environment to use KiCad's Python."""
    print("KiCad Laser Tracer - Setup")
    print("=" * 40)
    print()

    # Find KiCad's Python
    print("Discovering KiCad installation...")
    kicad_python = get_kicad_python_path()

    if not kicad_python:
        print("ERROR: Could not find KiCad's Python interpreter.")
        print()
        print("Please ensure KiCad is installed in a standard location:")
        print("  - macOS: /Applications/KiCad/KiCad.app")
        print("  - Linux: /usr or /usr/local")
        print("  - Windows: C:\\Program Files\\KiCad")
        sys.exit(1)

    kicad_python_path = Path(kicad_python)
    if not kicad_python_path.exists():
        print(f"ERROR: KiCad Python not found at: {kicad_python}")
        sys.exit(1)

    print(f"Found KiCad Python: {kicad_python}")
    print()

    # Check if we're already using the right Python
    current_python = sys.executable
    if Path(current_python).resolve() == kicad_python_path.resolve():
        print("You're already using KiCad's Python.")
        print()
        print("Running kigadgets setup...")
        subprocess.run([sys.executable, "-m", "kigadgets"], check=False)
        print()
        print("Setup complete! You can now run:")
        print("  uv run kicad-laser-tracer <your_pcb.kicad_pcb> -o output")
        return

    # Need to recreate venv with KiCad's Python
    print("Current Python is not KiCad's Python.")
    print()
    print("To use this tool, recreate your virtual environment with KiCad's Python:")
    print()
    print(f"  rm -rf .venv")
    print(f"  uv venv --python {kicad_python}")
    print(f"  uv pip install -e .")
    print(f"  uv run python -m kigadgets")
    print()
    print("Then you can run:")
    print("  uv run kicad-laser-tracer <your_pcb.kicad_pcb> -o output")


if __name__ == "__main__":
    main()
