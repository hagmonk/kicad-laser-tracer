#!/usr/bin/env python3
"""
Command-line interface for PCB Isolation Router.

Supports automatic re-execution with KiCad's Python if needed.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def get_kicad_python_path():
    """Use kigadgets to discover KiCad's Python interpreter path."""
    # Suppress kigadgets' verbose output at file descriptor level
    # (kigadgets may bypass Python's stdout/stderr)
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stdout = os.dup(1)
    old_stderr = os.dup(2)

    try:
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)

        from kigadgets.environment import get_default_paths
        paths = get_default_paths()
        kipython_paths = paths.get('kipython', [])
        if kipython_paths:
            return kipython_paths[0]
    except Exception:
        pass
    finally:
        os.dup2(old_stdout, 1)
        os.dup2(old_stderr, 2)
        os.close(devnull)
        os.close(old_stdout)
        os.close(old_stderr)

    return None


def is_running_with_kicad_python():
    """Check if we're running with KiCad's Python by comparing executable paths."""
    kicad_python = get_kicad_python_path()
    if not kicad_python:
        return False

    # Compare resolved paths
    current_python = Path(sys.executable).resolve()
    kicad_python_path = Path(kicad_python).resolve()

    # Check if we're running KiCad's Python (or a symlink to it)
    return current_python == kicad_python_path


def reexec_with_kicad_python():
    """Re-execute this script with KiCad's Python."""
    kicad_python = get_kicad_python_path()

    if not kicad_python:
        print("ERROR: Could not find KiCad's Python interpreter.", file=sys.stderr)
        print("Please ensure KiCad is installed.", file=sys.stderr)
        sys.exit(1)

    if not Path(kicad_python).exists():
        print(f"ERROR: KiCad Python not found at: {kicad_python}", file=sys.stderr)
        sys.exit(1)

    # Re-execute with KiCad's Python
    env = os.environ.copy()

    # Build PYTHONPATH with our package source directory only
    # We don't include the current env's site-packages because kigadgets
    # from a different Python version causes issues with pcbnew loading
    package_dir = Path(__file__).parent.parent
    paths_to_add = [str(package_dir)]

    existing_path = env.get('PYTHONPATH', '')
    new_path = ':'.join(paths_to_add)
    if existing_path:
        env['PYTHONPATH'] = f"{new_path}:{existing_path}"
    else:
        env['PYTHONPATH'] = new_path

    # Mark that we've already tried re-exec to prevent infinite loops
    env['_KICAD_LASER_TRACER_REEXEC'] = '1'

    # Re-run with the same arguments
    cmd = [kicad_python, '-m', 'kicad_laser_tracer'] + sys.argv[1:]

    try:
        # Use os.execve to replace this process entirely, avoiding cleanup issues
        # This prevents the original Python from running any cleanup that might
        # trigger kigadgets warnings
        os.execve(kicad_python, cmd, env)
    except Exception as e:
        print(f"ERROR: Failed to run with KiCad Python: {e}", file=sys.stderr)
        sys.exit(1)


def run_main():
    """The actual main logic that requires pcbnew."""
    from .core import (
        generate_isolation_svg,
        generate_edge_cuts_svg,
        generate_drill_holes_svg,
        generate_solder_mask_svg,
        generate_user_comments_svg,
        generate_multi_color_svg,
        generate_multi_color_svg_back
    )

    parser = argparse.ArgumentParser(
        description="Generate isolation routing SVGs using KiCad's native boolean operations"
    )
    parser.add_argument("pcb_file", type=Path, help="Input KiCad PCB file")
    parser.add_argument("-o", "--output", type=Path, default=Path("output"), help="Output directory")
    parser.add_argument("-s", "--side", choices=["front", "back", "both"], default="both",
                        help="Which side(s) to generate (default: both)")
    parser.add_argument("--drill", action="store_true", help="Generate drill holes SVG")
    parser.add_argument("--mask", action="store_true", help="Generate solder mask SVG")
    parser.add_argument("--comments", action="store_true", help="Generate User.Comments layer SVG")
    parser.add_argument("--all", action="store_true", help="Generate all outputs (isolation, drill, mask, edge cuts, comments)")
    parser.add_argument("--multi", action="store_true", help="Generate single multi-color SVG for XCS import")

    args = parser.parse_args()

    print("=" * 60)
    print("PCB Isolation Router - Using KiCad Native Boolean Operations")
    print("=" * 60)

    # Determine which copper layers to process based on side selection
    copper_layers = []
    if args.side in ["front", "both"]:
        copper_layers.append("F.Cu")
    if args.side in ["back", "both"]:
        copper_layers.append("B.Cu")

    # If multi-color mode, generate single SVG per side
    if args.multi:
        if "F.Cu" in copper_layers:
            generate_multi_color_svg(args.pcb_file, args.output, ["F.Cu"])
        if "B.Cu" in copper_layers:
            generate_multi_color_svg_back(args.pcb_file, args.output, ["B.Cu"])
    else:
        # Generate individual SVGs for each copper layer
        for layer in copper_layers:
            generate_isolation_svg(args.pcb_file, layer, args.output)
            print()

        # Generate drill holes if requested (only once, not per layer)
        if args.drill or args.all:
            generate_drill_holes_svg(args.pcb_file, args.output)
            print()

        # Generate solder mask if requested
        if args.mask or args.all:
            for layer in copper_layers:
                generate_solder_mask_svg(args.pcb_file, layer, args.output)
                print()

        # Generate User.Comments if requested
        if args.comments or args.all:
            generate_user_comments_svg(args.pcb_file, args.output)
            print()

        # Always generate edge cuts
        generate_edge_cuts_svg(args.pcb_file, args.output)

    print("\n" + "=" * 60)
    print("Done! Generated SVGs for laser cutting/etching.")
    print("=" * 60)


def main():
    """Entry point that handles Python version detection and re-execution."""
    # Check if we've already tried re-exec (prevent infinite loops)
    if os.environ.get('_KICAD_LASER_TRACER_REEXEC'):
        # We're in the re-exec'd process, just run
        run_main()
        return

    # Check if we can use pcbnew with current Python
    if is_running_with_kicad_python():
        run_main()
    else:
        # Need to re-exec with KiCad's Python
        reexec_with_kicad_python()


if __name__ == "__main__":
    main()
