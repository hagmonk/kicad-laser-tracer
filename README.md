# PCB Isolation Router

Generate isolation routing SVGs from KiCad PCB files for laser cutting/etching.

## Features

- Generates isolation paths (areas where copper needs to be removed) as filled SVG regions
- Uses KiCad's native boolean operations for accurate geometry
- Outputs separate SVG files for each copper layer plus edge cuts
- Compatible with laser cutters that support filled paths (e.g., XCS)

## Requirements

- KiCad 5.0 - 9.0 installed
- [uv](https://docs.astral.sh/uv/) package manager

## Quick Start

No setup required! The tool auto-detects your KiCad installation:

```bash
# Run directly with uvx (no installation needed)
uvx --from git+https://github.com/yourusername/kicad-laser-tracer \
    kicad-laser-tracer your_board.kicad_pcb -o output

# Or install locally
git clone https://github.com/yourusername/kicad-laser-tracer
cd kicad-laser-tracer
uv venv && uv pip install -e .
uv run kicad-laser-tracer your_board.kicad_pcb -o output
```

The CLI automatically detects if it's running with the wrong Python and re-executes itself with KiCad's bundled Python.

## Usage

```bash
# Generate isolation SVGs for a PCB
kicad-laser-tracer "your_pcb.kicad_pcb" -o output_dir

# Generate for specific side (front, back, or both)
kicad-laser-tracer "your_pcb.kicad_pcb" -s front -o output_dir

# Generate all outputs (isolation, drill holes, solder mask, edge cuts)
kicad-laser-tracer "your_pcb.kicad_pcb" --all -o output_dir

# Generate multi-color SVG for XCS import
kicad-laser-tracer "your_pcb.kicad_pcb" --multi -o output_dir
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

## How It Works

This tool uses KiCad's `pcbnew` Python module, which is bundled with KiCad. When you run the CLI:

1. It checks if it can access `pcbnew` with the current Python
2. If not, it uses `kigadgets` to discover your KiCad installation
3. It re-executes itself with KiCad's Python automatically

This means you can run it with any Python installation - it will find and use KiCad's Python transparently.

## Troubleshooting

### "Could not find KiCad's Python interpreter"

Make sure KiCad is installed in a standard location:
- **macOS**: `/Applications/KiCad/KiCad.app`
- **Linux**: `/usr` or `/usr/local`
- **Windows**: `C:\Program Files\KiCad`

### Debug output from wxWidgets

The wx "Debug: Adding duplicate image handler" messages are harmless warnings from KiCad's libraries when running outside the GUI. They don't affect the output.

## Note on KiCad 10+

The SWIG-based `pcbnew` Python bindings are deprecated as of KiCad 9.0 and planned for removal in KiCad 10.0 (February 2026). Future versions of this tool may need to migrate to KiCad's new IPC API.
