#!/usr/bin/env python3
"""
Core functionality for generating isolation routing SVGs using KiCad's native boolean operations.
"""

# kigadgets must be imported first - it sets up the path to pcbnew
import kigadgets  # noqa: F401
import pcbnew
import xml.etree.ElementTree as ET
from pathlib import Path

# SVG namespace
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

def shape_poly_set_to_svg_path(poly_set):
    """Convert a SHAPE_POLY_SET to SVG path data."""
    path_data = []
    
    # Iterate through all outlines in the poly set
    for outline_idx in range(poly_set.OutlineCount()):
        outline = poly_set.Outline(outline_idx)
        
        # Start path for this outline
        if outline.PointCount() > 0:
            first_point = outline.CPoint(0)
            x_mm = pcbnew.ToMM(first_point.x)
            y_mm = pcbnew.ToMM(first_point.y)
            path_data.append(f"M {x_mm:.6f} {y_mm:.6f}")
            
            # Add all other points
            for i in range(1, outline.PointCount()):
                point = outline.CPoint(i)
                x_mm = pcbnew.ToMM(point.x)
                y_mm = pcbnew.ToMM(point.y)
                path_data.append(f"L {x_mm:.6f} {y_mm:.6f}")
            
            # Close the path
            path_data.append("Z")
        
        # Handle holes in this outline
        for hole_idx in range(poly_set.HoleCount(outline_idx)):
            hole = poly_set.Hole(outline_idx, hole_idx)
            
            if hole.PointCount() > 0:
                first_point = hole.CPoint(0)
                x_mm = pcbnew.ToMM(first_point.x)
                y_mm = pcbnew.ToMM(first_point.y)
                path_data.append(f"M {x_mm:.6f} {y_mm:.6f}")
                
                for i in range(1, hole.PointCount()):
                    point = hole.CPoint(i)
                    x_mm = pcbnew.ToMM(point.x)
                    y_mm = pcbnew.ToMM(point.y)
                    path_data.append(f"L {x_mm:.6f} {y_mm:.6f}")
                
                path_data.append("Z")
    
    return " ".join(path_data)

def shape_poly_set_to_svg_path_mirrored(poly_set, board_center_x):
    """Convert a SHAPE_POLY_SET to SVG path data, mirrored across Y axis."""
    path_data = []
    
    # Iterate through all outlines in the poly set
    for outline_idx in range(poly_set.OutlineCount()):
        outline = poly_set.Outline(outline_idx)
        
        # Start path for this outline
        if outline.PointCount() > 0:
            first_point = outline.CPoint(0)
            x_mm = pcbnew.ToMM(first_point.x)
            y_mm = pcbnew.ToMM(first_point.y)
            # Mirror X coordinate across board center
            x_mirrored = 2 * board_center_x - x_mm
            path_data.append(f"M {x_mirrored:.6f} {y_mm:.6f}")
            
            # Add all other points
            for i in range(1, outline.PointCount()):
                point = outline.CPoint(i)
                x_mm = pcbnew.ToMM(point.x)
                y_mm = pcbnew.ToMM(point.y)
                x_mirrored = 2 * board_center_x - x_mm
                path_data.append(f"L {x_mirrored:.6f} {y_mm:.6f}")
            
            # Close the path
            path_data.append("Z")
        
        # Handle holes in this outline
        for hole_idx in range(poly_set.HoleCount(outline_idx)):
            hole = poly_set.Hole(outline_idx, hole_idx)
            
            if hole.PointCount() > 0:
                first_point = hole.CPoint(0)
                x_mm = pcbnew.ToMM(first_point.x)
                y_mm = pcbnew.ToMM(first_point.y)
                x_mirrored = 2 * board_center_x - x_mm
                path_data.append(f"M {x_mirrored:.6f} {y_mm:.6f}")
                
                for i in range(1, hole.PointCount()):
                    point = hole.CPoint(i)
                    x_mm = pcbnew.ToMM(point.x)
                    y_mm = pcbnew.ToMM(point.y)
                    x_mirrored = 2 * board_center_x - x_mm
                    path_data.append(f"L {x_mirrored:.6f} {y_mm:.6f}")
                
                path_data.append("Z")
    
    return " ".join(path_data)

def generate_isolation_svg(pcb_file: Path, layer_name: str, output_dir: Path):
    """Generate isolation routing SVG using KiCad's native boolean operations."""
    
    output_dir.mkdir(exist_ok=True)
    
    # Load board
    board = pcbnew.LoadBoard(str(pcb_file))
    
    # Get board bounding box for SVG dimensions
    bbox = board.ComputeBoundingBox(False)
    board_x_mm = pcbnew.ToMM(bbox.GetX())
    board_y_mm = pcbnew.ToMM(bbox.GetY())
    board_w_mm = pcbnew.ToMM(bbox.GetWidth())
    board_h_mm = pcbnew.ToMM(bbox.GetHeight())
    
    print(f"Processing {layer_name}...")
    print(f"  Board: ({board_x_mm:.2f}, {board_y_mm:.2f}) {board_w_mm:.2f}x{board_h_mm:.2f}mm")
    
    # Get board outline
    board_outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(board_outline, True)
    print(f"  Board outline: {board_outline.OutlineCount()} outlines, {board_outline.TotalVertices()} vertices")
    
    # Use exact board outline without deflation
    # This allows traces to go right up to the board edge
    board_area = pcbnew.SHAPE_POLY_SET(board_outline)
    
    # Collect all copper shapes on this layer
    copper_shapes = pcbnew.SHAPE_POLY_SET()
    layer_id = board.GetLayerID(layer_name)
    
    # Add tracks
    track_count = 0
    for track in board.GetTracks():
        if track.IsOnLayer(layer_id):
            track.TransformShapeToPolygon(copper_shapes, layer_id, 0, 10000, pcbnew.ERROR_INSIDE)
            track_count += 1
    
    # Add pads
    pad_count = 0
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.IsOnLayer(layer_id):
                pad.TransformShapeToPolygon(copper_shapes, layer_id, 0, 10000, pcbnew.ERROR_INSIDE)
                pad_count += 1
    
    # Add zones
    zone_count = 0
    for zone in board.Zones():
        if zone.IsOnLayer(layer_id):
            filled_polys = zone.GetFilledPolysList(layer_id)
            if filled_polys:
                copper_shapes.Append(filled_polys)
            zone_count += 1
    
    print(f"  Copper: {track_count} tracks, {pad_count} pads, {zone_count} zones")
    print(f"  Total copper shapes: {copper_shapes.OutlineCount()} outlines")
    
    # Perform boolean subtraction: board_area - copper = isolation
    # This removes both copper and the board edge
    isolation = pcbnew.SHAPE_POLY_SET(board_area)
    isolation.BooleanSubtract(copper_shapes)
    
    print(f"  Isolation: {isolation.OutlineCount()} outlines, {isolation.TotalVertices()} vertices")
    
    # Convert to SVG
    svg = ET.Element("svg")
    svg.set("xmlns", SVG_NS)
    svg.set("version", "1.1")
    svg.set("width", f"{board_w_mm}mm")
    svg.set("height", f"{board_h_mm}mm")
    svg.set("viewBox", f"{board_x_mm} {board_y_mm} {board_w_mm} {board_h_mm}")
    
    # Create path element for isolation
    # Use black for traces layer (areas to remove/etch)
    path = ET.Element("path")
    path.set("d", shape_poly_set_to_svg_path(isolation))
    path.set("fill", "#000000")  # Black for traces
    path.set("fill-rule", "evenodd")  # Important for holes
    svg.append(path)
    
    # Write SVG file
    output_file = output_dir / f"isolation_{layer_name.replace('.', '_')}.svg"
    tree = ET.ElementTree(svg)
    tree.write(str(output_file), encoding="utf-8", xml_declaration=True)
    
    print(f"  Generated: {output_file}")
    
    return output_file

def generate_edge_cuts_svg(pcb_file: Path, output_dir: Path):
    """Generate Edge.Cuts SVG."""
    
    board = pcbnew.LoadBoard(str(pcb_file))
    
    # Get board bounding box
    bbox = board.ComputeBoundingBox(False)
    board_x_mm = pcbnew.ToMM(bbox.GetX())
    board_y_mm = pcbnew.ToMM(bbox.GetY())
    board_w_mm = pcbnew.ToMM(bbox.GetWidth())
    board_h_mm = pcbnew.ToMM(bbox.GetHeight())
    
    # Get board outline
    board_outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(board_outline, True)
    
    # Convert to SVG
    svg = ET.Element("svg")
    svg.set("xmlns", SVG_NS)
    svg.set("version", "1.1")
    svg.set("width", f"{board_w_mm}mm")
    svg.set("height", f"{board_h_mm}mm")
    svg.set("viewBox", f"{board_x_mm} {board_y_mm} {board_w_mm} {board_h_mm}")
    
    # Create path for edge cuts (just the outline, not filled)
    # Use green for contour layer
    path = ET.Element("path")
    path.set("d", shape_poly_set_to_svg_path(board_outline))
    path.set("fill", "none")
    path.set("stroke", "#00ff00")  # Green for contour
    path.set("stroke-width", "0.1")
    svg.append(path)
    
    # Write SVG
    output_file = output_dir / "edge_cuts.svg"
    tree = ET.ElementTree(svg)
    tree.write(str(output_file), encoding="utf-8", xml_declaration=True)
    
    print(f"Edge cuts: {output_file}")
    
    return output_file

def generate_drill_holes_svg(pcb_file: Path, output_dir: Path):
    """Generate drill holes SVG."""
    
    output_dir.mkdir(exist_ok=True)
    
    # Load board
    board = pcbnew.LoadBoard(str(pcb_file))
    
    # Get board bounding box for SVG dimensions
    bbox = board.ComputeBoundingBox(False)
    board_x_mm = pcbnew.ToMM(bbox.GetX())
    board_y_mm = pcbnew.ToMM(bbox.GetY())
    board_w_mm = pcbnew.ToMM(bbox.GetWidth())
    board_h_mm = pcbnew.ToMM(bbox.GetHeight())
    
    print("Processing drill holes...")
    
    # Convert to SVG
    svg = ET.Element("svg")
    svg.set("xmlns", SVG_NS)
    svg.set("version", "1.1")
    svg.set("width", f"{board_w_mm}mm")
    svg.set("height", f"{board_h_mm}mm")
    svg.set("viewBox", f"{board_x_mm} {board_y_mm} {board_w_mm} {board_h_mm}")
    
    hole_count = 0
    
    # Get drill holes from pads
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            drill_size = pad.GetDrillSize()
            if drill_size.x > 0 and drill_size.y > 0:
                pos = pad.GetPosition()
                x_mm = pcbnew.ToMM(pos.x)
                y_mm = pcbnew.ToMM(pos.y)
                
                if drill_size.x == drill_size.y:
                    # Circular hole
                    radius_mm = pcbnew.ToMM(drill_size.x) / 2
                    circle = ET.Element("circle")
                    circle.set("cx", f"{x_mm:.6f}")
                    circle.set("cy", f"{y_mm:.6f}")
                    circle.set("r", f"{radius_mm:.6f}")
                    circle.set("fill", "#ff7f56")  # Orange (Clean layer) for holes
                    svg.append(circle)
                else:
                    # Oval hole (slot)
                    width_mm = pcbnew.ToMM(drill_size.x)
                    height_mm = pcbnew.ToMM(drill_size.y)
                    angle = pad.GetOrientation() / 10.0  # Convert from tenths of degree
                    
                    rect = ET.Element("ellipse")
                    rect.set("cx", f"{x_mm:.6f}")
                    rect.set("cy", f"{y_mm:.6f}")
                    rect.set("rx", f"{width_mm/2:.6f}")
                    rect.set("ry", f"{height_mm/2:.6f}")
                    if angle != 0:
                        rect.set("transform", f"rotate({angle} {x_mm} {y_mm})")
                    rect.set("fill", "#ff7f56")  # Orange (Clean layer) for holes
                    svg.append(rect)
                
                hole_count += 1
    
    # Get vias
    for track in board.GetTracks():
        if track.GetClass() == "PCB_VIA":
            via = track
            drill_value = via.GetDrillValue()
            if drill_value > 0:
                pos = via.GetPosition()
                x_mm = pcbnew.ToMM(pos.x)
                y_mm = pcbnew.ToMM(pos.y)
                radius_mm = pcbnew.ToMM(drill_value) / 2
                
                circle = ET.Element("circle")
                circle.set("cx", f"{x_mm:.6f}")
                circle.set("cy", f"{y_mm:.6f}")
                circle.set("r", f"{radius_mm:.6f}")
                circle.set("fill", "#000000")
                svg.append(circle)
                
                hole_count += 1
    
    print(f"  Found {hole_count} drill holes")
    
    # Write SVG
    output_file = output_dir / "drill_holes.svg"
    tree = ET.ElementTree(svg)
    tree.write(str(output_file), encoding="utf-8", xml_declaration=True)
    
    print(f"  Generated: {output_file}")
    
    return output_file

def generate_solder_mask_svg(pcb_file: Path, layer_name: str, output_dir: Path):
    """Generate solder mask SVG (areas where solder mask should be removed)."""
    
    output_dir.mkdir(exist_ok=True)
    
    # Load board
    board = pcbnew.LoadBoard(str(pcb_file))
    
    # Get board bounding box for SVG dimensions
    bbox = board.ComputeBoundingBox(False)
    board_x_mm = pcbnew.ToMM(bbox.GetX())
    board_y_mm = pcbnew.ToMM(bbox.GetY())
    board_w_mm = pcbnew.ToMM(bbox.GetWidth())
    board_h_mm = pcbnew.ToMM(bbox.GetHeight())
    
    print(f"Processing solder mask for {layer_name}...")
    
    # Determine which solder mask layer to use
    if "F" in layer_name:
        mask_layer = "F.Mask"
    else:
        mask_layer = "B.Mask"
    
    mask_layer_id = board.GetLayerID(mask_layer)
    
    # Collect all solder mask openings
    mask_openings = pcbnew.SHAPE_POLY_SET()
    
    # Add pad openings
    pad_count = 0
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.IsOnLayer(mask_layer_id):
                # Use default solder mask margin (typically 0.05mm)
                # margin = pcbnew.FromMM(0.05)
                margin = pcbnew.FromMM(0)
                pad.TransformShapeToPolygon(mask_openings, mask_layer_id, margin, 10000, pcbnew.ERROR_INSIDE)
                pad_count += 1
    
    # Add any explicit mask openings from zones
    zone_count = 0
    for zone in board.Zones():
        if zone.IsOnLayer(mask_layer_id):
            filled_polys = zone.GetFilledPolysList(mask_layer_id)
            if filled_polys:
                mask_openings.Append(filled_polys)
            zone_count += 1
    
    # Add via openings - vias need solder mask removal on both sides
    via_count = 0
    for track in board.GetTracks():
        if track.GetClass() == "PCB_VIA":
            via = track
            # Vias appear on both front and back mask layers
            # Get via position and size
            pos = via.GetPosition()
            # Via size is the outer diameter (copper annular ring)
            via_size = via.GetWidth()  # This is the copper diameter
            
            # Create a circle for the via opening
            # Add solder mask expansion (typically same as pads)
            margin = pcbnew.FromMM(0)  # Using same margin as pads
            
            # Create a circular shape for the via
            via_shape = pcbnew.SHAPE_POLY_SET()
            # We need to create a circle at the via position with radius = (via_size + margin) / 2
            radius = (via_size + margin) / 2
            
            # Create circle using segments (KiCad uses polygons for circles)
            circle_points = []
            num_segments = 32  # Number of segments for circle approximation
            import math
            for i in range(num_segments):
                angle = 2 * math.pi * i / num_segments
                x = pos.x + int(radius * math.cos(angle))
                y = pos.y + int(radius * math.sin(angle))
                circle_points.append(pcbnew.VECTOR2I(x, y))
            
            # Create the polygon from points
            via_poly = pcbnew.SHAPE_POLY_SET()
            via_poly.NewOutline()
            for pt in circle_points:
                via_poly.Append(pt)
            
            mask_openings.Append(via_poly)
            via_count += 1
    
    print(f"  Mask openings: {pad_count} pads, {via_count} vias, {zone_count} zones")
    print(f"  Total openings: {mask_openings.OutlineCount()} outlines")
    
    # Convert to SVG
    svg = ET.Element("svg")
    svg.set("xmlns", SVG_NS)
    svg.set("version", "1.1")
    svg.set("width", f"{board_w_mm}mm")
    svg.set("height", f"{board_h_mm}mm")
    svg.set("viewBox", f"{board_x_mm} {board_y_mm} {board_w_mm} {board_h_mm}")
    
    # Create path element for mask openings
    # Use yellow for mask layer
    if mask_openings.OutlineCount() > 0:
        path = ET.Element("path")
        path.set("d", shape_poly_set_to_svg_path(mask_openings))
        path.set("fill", "#ffff00")  # Yellow for mask
        path.set("fill-rule", "evenodd")
        svg.append(path)
    
    # Write SVG file
    output_file = output_dir / f"solder_mask_{layer_name.replace('.', '_')}.svg"
    tree = ET.ElementTree(svg)
    tree.write(str(output_file), encoding="utf-8", xml_declaration=True)
    
    print(f"  Generated: {output_file}")
    
    return output_file

def generate_user_comments_svg(pcb_file: Path, output_dir: Path):
    """Generate User.Comments layer SVG (cutting/scoring lines)."""
    
    output_dir.mkdir(exist_ok=True)
    
    # Load board
    board = pcbnew.LoadBoard(str(pcb_file))
    
    # Get board bounding box for SVG dimensions
    bbox = board.ComputeBoundingBox(False)
    board_x_mm = pcbnew.ToMM(bbox.GetX())
    board_y_mm = pcbnew.ToMM(bbox.GetY())
    board_w_mm = pcbnew.ToMM(bbox.GetWidth())
    board_h_mm = pcbnew.ToMM(bbox.GetHeight())
    
    print("Processing User.Comments layer...")
    
    # Get User.Comments layer ID
    comments_layer_id = board.GetLayerID("User.Comments")
    
    # Convert to SVG
    svg = ET.Element("svg")
    svg.set("xmlns", SVG_NS)
    svg.set("version", "1.1")
    svg.set("width", f"{board_w_mm}mm")
    svg.set("height", f"{board_h_mm}mm")
    svg.set("viewBox", f"{board_x_mm} {board_y_mm} {board_w_mm} {board_h_mm}")
    
    # Collect all drawings on User.Comments layer
    drawing_count = 0
    for drawing in board.GetDrawings():
        if drawing.IsOnLayer(comments_layer_id):
            if drawing.GetClass() == "PCB_SHAPE":
                shape = drawing
                shape_type = shape.GetShape()
                
                # Handle different shape types
                if shape_type == pcbnew.SHAPE_T_SEGMENT:
                    # Line segment
                    start = shape.GetStart()
                    end = shape.GetEnd()
                    line = ET.Element("line")
                    line.set("x1", f"{pcbnew.ToMM(start.x):.6f}")
                    line.set("y1", f"{pcbnew.ToMM(start.y):.6f}")
                    line.set("x2", f"{pcbnew.ToMM(end.x):.6f}")
                    line.set("y2", f"{pcbnew.ToMM(end.y):.6f}")
                    line.set("stroke", "#00befe")  # Cyan/light blue like contour
                    line.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                    line.set("fill", "none")
                    svg.append(line)
                    drawing_count += 1
                    
                elif shape_type == pcbnew.SHAPE_T_RECT:
                    # Rectangle
                    start = shape.GetStart()
                    end = shape.GetEnd()
                    x = min(pcbnew.ToMM(start.x), pcbnew.ToMM(end.x))
                    y = min(pcbnew.ToMM(start.y), pcbnew.ToMM(end.y))
                    width = abs(pcbnew.ToMM(end.x) - pcbnew.ToMM(start.x))
                    height = abs(pcbnew.ToMM(end.y) - pcbnew.ToMM(start.y))
                    rect = ET.Element("rect")
                    rect.set("x", f"{x:.6f}")
                    rect.set("y", f"{y:.6f}")
                    rect.set("width", f"{width:.6f}")
                    rect.set("height", f"{height:.6f}")
                    rect.set("stroke", "#00befe")
                    rect.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                    rect.set("fill", "none")
                    svg.append(rect)
                    drawing_count += 1
                    
                elif shape_type == pcbnew.SHAPE_T_CIRCLE:
                    # Circle
                    center = shape.GetCenter()
                    radius = shape.GetRadius()
                    circle = ET.Element("circle")
                    circle.set("cx", f"{pcbnew.ToMM(center.x):.6f}")
                    circle.set("cy", f"{pcbnew.ToMM(center.y):.6f}")
                    circle.set("r", f"{pcbnew.ToMM(radius):.6f}")
                    circle.set("stroke", "#00befe")
                    circle.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                    circle.set("fill", "none")
                    svg.append(circle)
                    drawing_count += 1
                    
                elif shape_type == pcbnew.SHAPE_T_POLY:
                    # Polygon/polyline
                    poly_shape = shape.GetPolyShape()
                    if poly_shape and poly_shape.OutlineCount() > 0:
                        path_data = shape_poly_set_to_svg_path(poly_shape)
                        path = ET.Element("path")
                        path.set("d", path_data)
                        path.set("stroke", "#00befe")
                        path.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                        path.set("fill", "none")
                        svg.append(path)
                        drawing_count += 1
    
    print(f"  Found {drawing_count} shapes on User.Comments")
    
    # Write SVG file
    output_file = output_dir / "user_comments.svg"
    tree = ET.ElementTree(svg)
    tree.write(str(output_file), encoding="utf-8", xml_declaration=True)
    
    print(f"  Generated: {output_file}")
    
    return output_file

def generate_multi_color_svg(pcb_file: Path, output_dir: Path, layers: list = ["F.Cu"]):
    """Generate a single multi-color SVG with all layers for XCS import."""
    
    output_dir.mkdir(exist_ok=True)
    
    # Load board
    board = pcbnew.LoadBoard(str(pcb_file))
    
    # Get board bounding box for SVG dimensions
    bbox = board.ComputeBoundingBox(False)
    board_x_mm = pcbnew.ToMM(bbox.GetX())
    board_y_mm = pcbnew.ToMM(bbox.GetY())
    board_w_mm = pcbnew.ToMM(bbox.GetWidth())
    board_h_mm = pcbnew.ToMM(bbox.GetHeight())
    
    print("Generating multi-color SVG...")
    print(f"  Board: ({board_x_mm:.2f}, {board_y_mm:.2f}) {board_w_mm:.2f}x{board_h_mm:.2f}mm")
    
    # Create main SVG
    svg = ET.Element("svg")
    svg.set("xmlns", SVG_NS)
    svg.set("version", "1.1")
    svg.set("width", f"{board_w_mm}mm")
    svg.set("height", f"{board_h_mm}mm")
    svg.set("viewBox", f"{board_x_mm} {board_y_mm} {board_w_mm} {board_h_mm}")
    
    # Get board outline
    board_outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(board_outline, True)
    
    # 1. Add edge cuts (green stroke for contour layer)
    edge_path = ET.Element("path")
    edge_path.set("d", shape_poly_set_to_svg_path(board_outline))
    edge_path.set("fill", "none")
    edge_path.set("stroke", "#00ff00")  # Green for contour
    edge_path.set("stroke-width", "0.1")
    svg.append(edge_path)
    
    # 2. Add isolation for each copper layer (black for traces)
    for layer_name in layers:
        board_area = pcbnew.SHAPE_POLY_SET(board_outline)
        copper_shapes = pcbnew.SHAPE_POLY_SET()
        layer_id = board.GetLayerID(layer_name)
        
        # Add tracks
        for track in board.GetTracks():
            if track.IsOnLayer(layer_id):
                track.TransformShapeToPolygon(copper_shapes, layer_id, 0, 10000, pcbnew.ERROR_INSIDE)
        
        # Add pads
        for footprint in board.GetFootprints():
            for pad in footprint.Pads():
                if pad.IsOnLayer(layer_id):
                    pad.TransformShapeToPolygon(copper_shapes, layer_id, 0, 10000, pcbnew.ERROR_INSIDE)
        
        # Add zones
        for zone in board.Zones():
            if zone.IsOnLayer(layer_id):
                filled_polys = zone.GetFilledPolysList(layer_id)
                if filled_polys:
                    copper_shapes.Append(filled_polys)
        
        # Boolean subtraction: board - copper = isolation
        isolation = pcbnew.SHAPE_POLY_SET(board_area)
        isolation.BooleanSubtract(copper_shapes)
        
        if isolation.OutlineCount() > 0:
            isolation_path = ET.Element("path")
            isolation_path.set("d", shape_poly_set_to_svg_path(isolation))
            isolation_path.set("fill", "#000000")  # Black for traces
            isolation_path.set("fill-rule", "evenodd")
            svg.append(isolation_path)
    
    # 3. Add drill holes (orange for holes layer)
    hole_count = 0
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            drill_size = pad.GetDrillSize()
            if drill_size.x > 0 and drill_size.y > 0:
                pos = pad.GetPosition()
                x_mm = pcbnew.ToMM(pos.x)
                y_mm = pcbnew.ToMM(pos.y)
                
                if drill_size.x == drill_size.y:
                    # Circular hole
                    radius_mm = pcbnew.ToMM(drill_size.x) / 2
                    circle = ET.Element("circle")
                    circle.set("cx", f"{x_mm:.6f}")
                    circle.set("cy", f"{y_mm:.6f}")
                    circle.set("r", f"{radius_mm:.6f}")
                    circle.set("fill", "#ff7f56")  # Orange for holes
                    svg.append(circle)
                    hole_count += 1
    
    # Add vias
    for track in board.GetTracks():
        if track.GetClass() == "PCB_VIA":
            via = track
            drill_value = via.GetDrillValue()
            if drill_value > 0:
                pos = via.GetPosition()
                x_mm = pcbnew.ToMM(pos.x)
                y_mm = pcbnew.ToMM(pos.y)
                radius_mm = pcbnew.ToMM(drill_value) / 2
                
                circle = ET.Element("circle")
                circle.set("cx", f"{x_mm:.6f}")
                circle.set("cy", f"{y_mm:.6f}")
                circle.set("r", f"{radius_mm:.6f}")
                circle.set("fill", "#ff7f56")  # Orange for holes
                svg.append(circle)
                hole_count += 1
    
    # 4. Add solder mask (yellow for mask layer)
    for layer_name in layers:
        if "F" in layer_name:
            mask_layer = "F.Mask"
        else:
            mask_layer = "B.Mask"
        
        mask_layer_id = board.GetLayerID(mask_layer)
        mask_openings = pcbnew.SHAPE_POLY_SET()
        
        for footprint in board.GetFootprints():
            for pad in footprint.Pads():
                if pad.IsOnLayer(mask_layer_id):
                    margin = pcbnew.FromMM(0)
                    pad.TransformShapeToPolygon(mask_openings, mask_layer_id, margin, 10000, pcbnew.ERROR_INSIDE)
        
        # Add via openings to mask
        import math
        for track in board.GetTracks():
            if track.GetClass() == "PCB_VIA":
                via = track
                pos = via.GetPosition()
                via_size = via.GetWidth()
                margin = pcbnew.FromMM(0)
                radius = (via_size + margin) / 2
                
                # Create circle using segments
                circle_points = []
                num_segments = 32
                for i in range(num_segments):
                    angle = 2 * math.pi * i / num_segments
                    x = pos.x + int(radius * math.cos(angle))
                    y = pos.y + int(radius * math.sin(angle))
                    circle_points.append(pcbnew.VECTOR2I(x, y))
                
                via_poly = pcbnew.SHAPE_POLY_SET()
                via_poly.NewOutline()
                for pt in circle_points:
                    via_poly.Append(pt)
                
                mask_openings.Append(via_poly)
        
        if mask_openings.OutlineCount() > 0:
            mask_path = ET.Element("path")
            mask_path.set("d", shape_poly_set_to_svg_path(mask_openings))
            mask_path.set("fill", "#ffff00")  # Yellow for mask
            mask_path.set("fill-rule", "evenodd")
            svg.append(mask_path)
    
    # 5. Add User.Comments layer (cyan/blue for additional cutting/scoring)
    comments_layer_id = board.GetLayerID("User.Comments")
    comments_count = 0
    for drawing in board.GetDrawings():
        if drawing.IsOnLayer(comments_layer_id):
            if drawing.GetClass() == "PCB_SHAPE":
                shape = drawing
                shape_type = shape.GetShape()
                
                if shape_type == pcbnew.SHAPE_T_SEGMENT:
                    start = shape.GetStart()
                    end = shape.GetEnd()
                    line = ET.Element("line")
                    line.set("x1", f"{pcbnew.ToMM(start.x):.6f}")
                    line.set("y1", f"{pcbnew.ToMM(start.y):.6f}")
                    line.set("x2", f"{pcbnew.ToMM(end.x):.6f}")
                    line.set("y2", f"{pcbnew.ToMM(end.y):.6f}")
                    line.set("stroke", "#00befe")  # Cyan like contour
                    line.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                    line.set("fill", "none")
                    svg.append(line)
                    comments_count += 1
                elif shape_type == pcbnew.SHAPE_T_RECT:
                    start = shape.GetStart()
                    end = shape.GetEnd()
                    x = min(pcbnew.ToMM(start.x), pcbnew.ToMM(end.x))
                    y = min(pcbnew.ToMM(start.y), pcbnew.ToMM(end.y))
                    width = abs(pcbnew.ToMM(end.x) - pcbnew.ToMM(start.x))
                    height = abs(pcbnew.ToMM(end.y) - pcbnew.ToMM(start.y))
                    rect = ET.Element("rect")
                    rect.set("x", f"{x:.6f}")
                    rect.set("y", f"{y:.6f}")
                    rect.set("width", f"{width:.6f}")
                    rect.set("height", f"{height:.6f}")
                    rect.set("stroke", "#00befe")
                    rect.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                    rect.set("fill", "none")
                    svg.append(rect)
                    comments_count += 1
                elif shape_type == pcbnew.SHAPE_T_CIRCLE:
                    center = shape.GetCenter()
                    radius = shape.GetRadius()
                    circle = ET.Element("circle")
                    circle.set("cx", f"{pcbnew.ToMM(center.x):.6f}")
                    circle.set("cy", f"{pcbnew.ToMM(center.y):.6f}")
                    circle.set("r", f"{pcbnew.ToMM(radius):.6f}")
                    circle.set("stroke", "#00befe")
                    circle.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                    circle.set("fill", "none")
                    svg.append(circle)
                    comments_count += 1
                elif shape_type == pcbnew.SHAPE_T_POLY:
                    poly_shape = shape.GetPolyShape()
                    if poly_shape and poly_shape.OutlineCount() > 0:
                        path_data = shape_poly_set_to_svg_path(poly_shape)
                        path = ET.Element("path")
                        path.set("d", path_data)
                        path.set("stroke", "#00befe")
                        path.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                        path.set("fill", "none")
                        svg.append(path)
                        comments_count += 1
    
    print(f"  Added {hole_count} drill holes")
    print(f"  Added {comments_count} User.Comments shapes")
    print(f"  Added isolation, edge cuts, and solder mask")
    
    # Write SVG file
    output_file = output_dir / "multi_color_pcb.svg"
    tree = ET.ElementTree(svg)
    tree.write(str(output_file), encoding="utf-8", xml_declaration=True)
    
    print(f"  Generated: {output_file}")
    
    return output_file

def generate_multi_color_svg_back(pcb_file: Path, output_dir: Path, layers: list = ["B.Cu"]):
    """Generate a single multi-color SVG with all back layers for XCS import (mirrored)."""
    
    output_dir.mkdir(exist_ok=True)
    
    # Load board
    board = pcbnew.LoadBoard(str(pcb_file))
    
    # Get board bounding box for SVG dimensions
    bbox = board.ComputeBoundingBox(False)
    board_x_mm = pcbnew.ToMM(bbox.GetX())
    board_y_mm = pcbnew.ToMM(bbox.GetY())
    board_w_mm = pcbnew.ToMM(bbox.GetWidth())
    board_h_mm = pcbnew.ToMM(bbox.GetHeight())
    board_center_x = board_x_mm + board_w_mm / 2
    
    print("Generating multi-color SVG for back layers (mirrored)...")
    print(f"  Board: ({board_x_mm:.2f}, {board_y_mm:.2f}) {board_w_mm:.2f}x{board_h_mm:.2f}mm")
    
    # Create main SVG
    svg = ET.Element("svg")
    svg.set("xmlns", SVG_NS)
    svg.set("version", "1.1")
    svg.set("width", f"{board_w_mm}mm")
    svg.set("height", f"{board_h_mm}mm")
    svg.set("viewBox", f"{board_x_mm} {board_y_mm} {board_w_mm} {board_h_mm}")
    
    # Get board outline
    board_outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(board_outline, True)
    
    # 1. Add edge cuts (green stroke for contour layer) - mirrored
    edge_path = ET.Element("path")
    edge_path.set("d", shape_poly_set_to_svg_path_mirrored(board_outline, board_center_x))
    edge_path.set("fill", "none")
    edge_path.set("stroke", "#00ff00")  # Green for contour
    edge_path.set("stroke-width", "0.1")
    svg.append(edge_path)
    
    # 2. Add isolation for each back copper layer (black for traces) - mirrored
    for layer_name in layers:
        if "B." in layer_name:
            board_area = pcbnew.SHAPE_POLY_SET(board_outline)
            copper_shapes = pcbnew.SHAPE_POLY_SET()
            layer_id = board.GetLayerID(layer_name)
            
            # Add tracks
            for track in board.GetTracks():
                if track.IsOnLayer(layer_id):
                    track.TransformShapeToPolygon(copper_shapes, layer_id, 0, 10000, pcbnew.ERROR_INSIDE)
            
            # Add pads
            for footprint in board.GetFootprints():
                for pad in footprint.Pads():
                    if pad.IsOnLayer(layer_id):
                        pad.TransformShapeToPolygon(copper_shapes, layer_id, 0, 10000, pcbnew.ERROR_INSIDE)
            
            # Add zones
            for zone in board.Zones():
                if zone.IsOnLayer(layer_id):
                    filled_polys = zone.GetFilledPolysList(layer_id)
                    if filled_polys:
                        copper_shapes.Append(filled_polys)
            
            # Boolean subtraction: board - copper = isolation
            isolation = pcbnew.SHAPE_POLY_SET(board_area)
            isolation.BooleanSubtract(copper_shapes)
            
            if isolation.OutlineCount() > 0:
                isolation_path = ET.Element("path")
                isolation_path.set("d", shape_poly_set_to_svg_path_mirrored(isolation, board_center_x))
                isolation_path.set("fill", "#000000")  # Black for traces
                isolation_path.set("fill-rule", "evenodd")
                svg.append(isolation_path)
    
    # 3. Add drill holes (orange for holes layer) - mirrored positions
    hole_count = 0
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            drill_size = pad.GetDrillSize()
            if drill_size.x > 0 and drill_size.y > 0:
                pos = pad.GetPosition()
                x_mm = pcbnew.ToMM(pos.x)
                y_mm = pcbnew.ToMM(pos.y)
                x_mirrored = 2 * board_center_x - x_mm
                
                if drill_size.x == drill_size.y:
                    # Circular hole
                    radius_mm = pcbnew.ToMM(drill_size.x) / 2
                    circle = ET.Element("circle")
                    circle.set("cx", f"{x_mirrored:.6f}")
                    circle.set("cy", f"{y_mm:.6f}")
                    circle.set("r", f"{radius_mm:.6f}")
                    circle.set("fill", "#ff7f56")  # Orange for holes
                    svg.append(circle)
                    hole_count += 1
    
    # Add vias - mirrored positions
    for track in board.GetTracks():
        if track.GetClass() == "PCB_VIA":
            via = track
            drill_value = via.GetDrillValue()
            if drill_value > 0:
                pos = via.GetPosition()
                x_mm = pcbnew.ToMM(pos.x)
                y_mm = pcbnew.ToMM(pos.y)
                x_mirrored = 2 * board_center_x - x_mm
                radius_mm = pcbnew.ToMM(drill_value) / 2
                
                circle = ET.Element("circle")
                circle.set("cx", f"{x_mirrored:.6f}")
                circle.set("cy", f"{y_mm:.6f}")
                circle.set("r", f"{radius_mm:.6f}")
                circle.set("fill", "#ff7f56")  # Orange for holes
                svg.append(circle)
                hole_count += 1
    
    # 4. Add solder mask for back layers (yellow for mask layer) - mirrored
    for layer_name in layers:
        if "B." in layer_name:
            mask_layer = "B.Mask"
            mask_layer_id = board.GetLayerID(mask_layer)
            mask_openings = pcbnew.SHAPE_POLY_SET()
            
            for footprint in board.GetFootprints():
                for pad in footprint.Pads():
                    if pad.IsOnLayer(mask_layer_id):
                        margin = pcbnew.FromMM(0)
                        pad.TransformShapeToPolygon(mask_openings, mask_layer_id, margin, 10000, pcbnew.ERROR_INSIDE)
            
            # Add via openings to mask - vias need openings on both sides
            import math
            for track in board.GetTracks():
                if track.GetClass() == "PCB_VIA":
                    via = track
                    pos = via.GetPosition()
                    via_size = via.GetWidth()  # This is the copper diameter
                    margin = pcbnew.FromMM(0)
                    radius = (via_size + margin) / 2
                    
                    # Create circle using segments (KiCad uses polygons for circles)
                    circle_points = []
                    num_segments = 32
                    for i in range(num_segments):
                        angle = 2 * math.pi * i / num_segments
                        x = pos.x + int(radius * math.cos(angle))
                        y = pos.y + int(radius * math.sin(angle))
                        circle_points.append(pcbnew.VECTOR2I(x, y))
                    
                    via_poly = pcbnew.SHAPE_POLY_SET()
                    via_poly.NewOutline()
                    for pt in circle_points:
                        via_poly.Append(pt)
                    
                    mask_openings.Append(via_poly)
            
            if mask_openings.OutlineCount() > 0:
                mask_path = ET.Element("path")
                mask_path.set("d", shape_poly_set_to_svg_path_mirrored(mask_openings, board_center_x))
                mask_path.set("fill", "#ffff00")  # Yellow for mask
                mask_path.set("fill-rule", "evenodd")
                svg.append(mask_path)
    
    # 5. Add User.Comments layer (cyan/blue) - mirrored
    comments_layer_id = board.GetLayerID("User.Comments")
    comments_count = 0
    for drawing in board.GetDrawings():
        if drawing.IsOnLayer(comments_layer_id):
            if drawing.GetClass() == "PCB_SHAPE":
                shape = drawing
                shape_type = shape.GetShape()
                
                if shape_type == pcbnew.SHAPE_T_SEGMENT:
                    start = shape.GetStart()
                    end = shape.GetEnd()
                    start_x_mirrored = 2 * board_center_x - pcbnew.ToMM(start.x)
                    end_x_mirrored = 2 * board_center_x - pcbnew.ToMM(end.x)
                    line = ET.Element("line")
                    line.set("x1", f"{start_x_mirrored:.6f}")
                    line.set("y1", f"{pcbnew.ToMM(start.y):.6f}")
                    line.set("x2", f"{end_x_mirrored:.6f}")
                    line.set("y2", f"{pcbnew.ToMM(end.y):.6f}")
                    line.set("stroke", "#00befe")  # Cyan like contour
                    line.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                    line.set("fill", "none")
                    svg.append(line)
                    comments_count += 1
                elif shape_type == pcbnew.SHAPE_T_RECT:
                    start = shape.GetStart()
                    end = shape.GetEnd()
                    start_x_mm = pcbnew.ToMM(start.x)
                    end_x_mm = pcbnew.ToMM(end.x)
                    # Mirror the x coordinates
                    start_x_mirrored = 2 * board_center_x - start_x_mm
                    end_x_mirrored = 2 * board_center_x - end_x_mm
                    x = min(start_x_mirrored, end_x_mirrored)
                    y = min(pcbnew.ToMM(start.y), pcbnew.ToMM(end.y))
                    width = abs(end_x_mirrored - start_x_mirrored)
                    height = abs(pcbnew.ToMM(end.y) - pcbnew.ToMM(start.y))
                    rect = ET.Element("rect")
                    rect.set("x", f"{x:.6f}")
                    rect.set("y", f"{y:.6f}")
                    rect.set("width", f"{width:.6f}")
                    rect.set("height", f"{height:.6f}")
                    rect.set("stroke", "#00befe")
                    rect.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                    rect.set("fill", "none")
                    svg.append(rect)
                    comments_count += 1
                elif shape_type == pcbnew.SHAPE_T_CIRCLE:
                    center = shape.GetCenter()
                    radius = shape.GetRadius()
                    center_x_mirrored = 2 * board_center_x - pcbnew.ToMM(center.x)
                    circle = ET.Element("circle")
                    circle.set("cx", f"{center_x_mirrored:.6f}")
                    circle.set("cy", f"{pcbnew.ToMM(center.y):.6f}")
                    circle.set("r", f"{pcbnew.ToMM(radius):.6f}")
                    circle.set("stroke", "#00befe")
                    circle.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                    circle.set("fill", "none")
                    svg.append(circle)
                    comments_count += 1
                elif shape_type == pcbnew.SHAPE_T_POLY:
                    poly_shape = shape.GetPolyShape()
                    if poly_shape and poly_shape.OutlineCount() > 0:
                        path_data = shape_poly_set_to_svg_path_mirrored(poly_shape, board_center_x)
                        path = ET.Element("path")
                        path.set("d", path_data)
                        path.set("stroke", "#00befe")
                        path.set("stroke-width", f"{pcbnew.ToMM(shape.GetWidth()):.3f}")
                        path.set("fill", "none")
                        svg.append(path)
                        comments_count += 1
    
    print(f"  Added {hole_count} drill holes")
    print(f"  Added {comments_count} User.Comments shapes")
    print(f"  Added isolation, edge cuts, and solder mask for back layers")
    
    # Write SVG file
    output_file = output_dir / "multi_color_pcb_back.svg"
    tree = ET.ElementTree(svg)
    tree.write(str(output_file), encoding="utf-8", xml_declaration=True)
    
    print(f"  Generated: {output_file}")
    
    return output_file