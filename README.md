# PCB Isolation Router

Generate isolation routing SVGs from KiCad PCB files for laser cutting/etching.

## Features

- Generates isolation paths (areas where copper needs to be removed) as filled SVG regions
- Uses KiCad's native boolean operations for accurate geometry
- Outputs separate SVG files for each copper layer plus edge cuts
- Compatible with laser cutters that support filled paths (e.g., XCS)

## Requirements

- KiCad installed (uses KiCad's Python with pcbnew module)
- Python 3.9+ (specifically KiCad's bundled Python)

## Installation

This package requires KiCad's Python installation which includes the `pcbnew` module.

### Using uv (recommended)

```bash
cd kicad-laser-tracer
uv pip install -e .
```

### Manual installation

```bash
cd kicad-laser-tracer
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9 -m pip install -e .
```

## Usage

```bash
# Generate isolation SVGs for a PCB
kicad-laser-tracer "your_pcb.kicad_pcb" -o output_dir

# Specify layers (default: F.Cu,B.Cu)
kicad-laser-tracer "your_pcb.kicad_pcb" -l "F.Cu,B.Cu,In1.Cu" -o output_dir
```

Or run directly with KiCad's Python:

```bash
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9 -m kicad_laser_tracer "your_pcb.kicad_pcb"
```

## Output

The tool generates:
- `isolation_F_Cu.svg` - Front copper isolation paths
- `isolation_B_Cu.svg` - Back copper isolation paths
- `edge_cuts.svg` - Board outline
- Additional isolation files for any other specified layers

All isolation SVGs contain filled paths representing areas where copper should be removed.