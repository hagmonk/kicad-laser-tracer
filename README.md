# PCB Isolation Router

Generate isolation routing SVGs from KiCad PCB files for laser cutting/etching.

## Features

- Generates isolation paths (areas where copper needs to be removed) as filled SVG regions
- Uses KiCad's native boolean operations for accurate geometry
- Outputs separate SVG files for each copper layer plus edge cuts
- Compatible with laser cutters that support filled paths (e.g., XCS)

## Requirements

- KiCad 5.0 - 9.0 installed
- [uv](https://docs.astral.sh/uv/) package manager (recommended)

## Installation

### Quick Start

```bash
cd kicad-laser-tracer

# Create a temporary venv and install
uv venv
uv pip install -e .

# Run setup to discover KiCad and get instructions
uv run kicad-laser-tracer-setup
```

The setup command will detect your KiCad installation and tell you exactly what commands to run.

### What the Setup Does

This tool uses KiCad's `pcbnew` Python module, which is a compiled C extension. It must run with KiCad's bundled Python interpreter. The setup command:

1. Uses `kigadgets` (included as a dependency) to auto-discover your KiCad installation
2. Tells you the correct `uv venv --python` command to create a compatible environment
3. Configures the pcbnew module path

## Usage

```bash
# Generate isolation SVGs for a PCB
uv run kicad-laser-tracer "your_pcb.kicad_pcb" -o output_dir

# Generate for specific side (front, back, or both)
uv run kicad-laser-tracer "your_pcb.kicad_pcb" -s front -o output_dir

# Generate all outputs (isolation, drill holes, solder mask, edge cuts)
uv run kicad-laser-tracer "your_pcb.kicad_pcb" --all -o output_dir

# Generate multi-color SVG for XCS import
uv run kicad-laser-tracer "your_pcb.kicad_pcb" --multi -o output_dir
```

## Output

The tool generates:
- `isolation_F_Cu.svg` - Front copper isolation paths
- `isolation_B_Cu.svg` - Back copper isolation paths
- `edge_cuts.svg` - Board outline
- `drill_holes.svg` - Drill hole locations (with `--drill` or `--all`)
- `solder_mask_*.svg` - Solder mask openings (with `--mask` or `--all`)
- `multi_color_pcb.svg` - Combined multi-layer SVG (with `--multi`)

All isolation SVGs contain filled paths representing areas where copper should be removed.

## Troubleshooting

### "Library not loaded" or shared object errors

Run `uv run kicad-laser-tracer-setup` - it will detect the problem and tell you how to fix it.

### "No module named pcbnew"

Run `uv run python -m kigadgets` to configure the pcbnew path discovery.

## Note on KiCad 10+

The SWIG-based `pcbnew` Python bindings are deprecated as of KiCad 9.0 and planned for removal in KiCad 10.0 (February 2026). Future versions of this tool may need to migrate to KiCad's new IPC API.
