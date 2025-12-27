#!/usr/bin/env python3
"""
Command-line interface for PCB Isolation Router.
"""

import argparse
from pathlib import Path
from .core import (
    generate_isolation_svg, 
    generate_edge_cuts_svg,
    generate_drill_holes_svg,
    generate_solder_mask_svg,
    generate_user_comments_svg,
    generate_multi_color_svg,
    generate_multi_color_svg_back
)

def main():
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

if __name__ == "__main__":
    main()