"""PCB Isolation Router - Generate isolation routing SVGs from KiCad PCB files."""

__version__ = "0.1.0"

from .core import (
    generate_isolation_svg, 
    generate_edge_cuts_svg,
    generate_drill_holes_svg,
    generate_solder_mask_svg,
    generate_user_comments_svg,
    generate_multi_color_svg,
    generate_multi_color_svg_back
)