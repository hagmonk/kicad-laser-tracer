"""PCB Isolation Router - Generate isolation routing SVGs from KiCad PCB files."""

__version__ = "0.1.0"

# Lazy imports - core requires pcbnew which needs KiCad's Python
def __getattr__(name):
    if name in (
        'generate_isolation_svg',
        'generate_edge_cuts_svg',
        'generate_drill_holes_svg',
        'generate_solder_mask_svg',
        'generate_user_comments_svg',
        'generate_multi_color_svg',
        'generate_multi_color_svg_back'
    ):
        from . import core
        return getattr(core, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")