"""Discovery and import of pcbnew module from KiCad installation."""

import os
import platform
import sys
from pathlib import Path


def find_pcbnew_paths():
    """Find potential paths where pcbnew module might be installed."""
    paths = []
    system = platform.system()
    
    if system == "Darwin":  # macOS
        # Standard KiCad installation paths on macOS
        kicad_apps = [
            "/Applications/KiCad/KiCad.app",
            "/Applications/Kicad.app",
            "/Applications/KiCad.app",
            Path.home() / "Applications" / "KiCad" / "KiCad.app",
        ]
        
        for app_path in kicad_apps:
            if isinstance(app_path, str):
                app_path = Path(app_path)
            if app_path.exists():
                # Common paths within the app bundle
                potential_paths = [
                    app_path / "Contents" / "Frameworks" / "Python.framework" / "Versions" / "Current" / "lib" / "python3.9" / "site-packages",
                    app_path / "Contents" / "Frameworks" / "Python.framework" / "Versions" / "3.9" / "lib" / "python3.9" / "site-packages",
                    app_path / "Contents" / "Frameworks" / "python" / "site-packages",
                ]
                paths.extend([str(p) for p in potential_paths if p.exists()])
    
    elif system == "Linux":
        # Standard KiCad installation paths on Linux
        paths.extend([
            "/usr/lib/python3/dist-packages",
            "/usr/local/lib/python3/dist-packages",
            "/usr/lib/kicad/lib/python3/dist-packages",
            "/usr/share/kicad/scripting",
        ])
    
    elif system == "Windows":
        # Standard KiCad installation paths on Windows
        paths.extend([
            r"C:\Program Files\KiCad\bin\Lib\site-packages",
            r"C:\Program Files\KiCad\lib\python3.9\site-packages",
            r"C:\Program Files (x86)\KiCad\bin\Lib\site-packages",
        ])
    
    # Check for environment variable override
    if "KICAD_PCBNEW_PATH" in os.environ:
        paths.insert(0, os.environ["KICAD_PCBNEW_PATH"])
    
    return paths


def import_pcbnew():
    """Import and return the pcbnew module from KiCad installation."""
    # If already imported, return it
    if "pcbnew" in sys.modules:
        return sys.modules["pcbnew"]
    
    # Try to find and import pcbnew
    paths = find_pcbnew_paths()
    
    for path in paths:
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            import pcbnew
            return pcbnew
        except ImportError:
            continue
    
    # Last attempt without path manipulation
    try:
        import pcbnew
        return pcbnew
    except ImportError:
        raise ImportError(
            "Could not find pcbnew module. Please ensure KiCad is installed "
            "or set KICAD_PCBNEW_PATH environment variable to the correct path."
        )