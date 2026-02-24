#!/usr/bin/env python3
"""
Generate Diagram - Main entry point for Excalidraw diagram generation.

This script takes text input, routes it to the appropriate diagram type,
generates the .excalidraw file, exports to PNG, and optionally copies to Obsidian.

Usage:
    python3 generate_diagram.py --text "User logs in, checks credentials..." --output /tmp/diagram
    python3 generate_diagram.py --text "..." --output /tmp/diagram --type flowchart
    python3 generate_diagram.py --text "..." --output /tmp/diagram --obsidian
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

# Import the diagram classes and router
from excalidraw_generator import (
    Diagram, Flowchart, ArchitectureDiagram, AutoLayoutFlowchart,
    SequenceDiagram, MindMap, TimelineDiagram, ERDiagram
)
from diagram_router import analyze_text


def generate_diagram_from_analysis(analysis: Dict[str, Any], output_path: str) -> Dict[str, Any]:
    """Generate diagram based on analysis results.
    
    Args:
        analysis: Result from diagram_router.analyze_text()
        output_path: Base output path (without extension)
        
    Returns:
        Dict with generation results
    """
    diagram_type = analysis["diagram_type"]
    elements = analysis["elements"]
    connections = analysis.get("connections", [])
    
    # Create appropriate diagram instance
    try:
        if diagram_type == "flowchart":
            diagram = _create_flowchart(elements, connections, analysis)
        elif diagram_type == "architecture":
            diagram = _create_architecture_diagram(elements, connections, analysis)
        elif diagram_type == "sequence":
            diagram = _create_sequence_diagram(elements, connections, analysis)
        elif diagram_type == "mindmap":
            diagram = _create_mindmap(elements, connections, analysis)
        elif diagram_type == "timeline":
            diagram = _create_timeline_diagram(elements, connections, analysis)
        elif diagram_type == "er":
            diagram = _create_er_diagram(elements, connections, analysis)
        else:  # simple diagram
            diagram = _create_simple_diagram(elements, connections, analysis)
    except Exception as e:
        # Fallback to simple diagram on error
        print(f"Warning: Failed to create {diagram_type} diagram: {e}", file=sys.stderr)
        print(f"Falling back to simple diagram", file=sys.stderr)
        diagram = _create_simple_diagram(elements, connections, analysis)
        diagram_type = "simple"
    
    # Save diagram
    excalidraw_path = f"{output_path}.excalidraw"
    diagram.save(excalidraw_path)
    
    return {
        "diagram": diagram,
        "type": diagram_type,
        "excalidraw_path": excalidraw_path,
        "analysis": analysis
    }


def _create_flowchart(elements: list, connections: list, analysis: dict) -> Flowchart:
    """Create a flowchart diagram."""
    flowchart = Flowchart(direction="vertical", spacing=100)
    
    if not elements:
        # Create a simple start->end flow
        flowchart.start("Start")
        flowchart.process("main", "Main Process")
        flowchart.end("End")
        flowchart.connect("__start__", "main")
        flowchart.connect("main", "__end__")
        return flowchart
    
    # Add start node
    flowchart.start("Start")
    previous_id = "__start__"
    
    # Process elements and connections
    for i, element in enumerate(elements):
        element_clean = element.strip().rstrip('.!?')
        
        # Detect decision nodes (questions, checks, conditions)
        if any(word in element_clean.lower() for word in ["check", "if", "validate", "verify", "decision", "?"]):
            node_id = f"decision_{i}"
            flowchart.decision(node_id, element_clean)
            
            # Connect from previous
            flowchart.connect(previous_id, node_id)
            
            # Add yes/no branches if we have connections
            yes_connections = [c for c in connections if c.get("from", "").lower() in element_clean.lower()]
            if yes_connections:
                for conn in yes_connections[:1]:  # Take first yes connection
                    next_id = f"process_{i}_yes"
                    flowchart.process(next_id, conn.get("to", "Continue"))
                    flowchart.connect(node_id, next_id, label="yes")
                    previous_id = next_id
            else:
                # Default yes branch
                next_id = f"process_{i}_continue"
                flowchart.process(next_id, "Continue")
                flowchart.connect(node_id, next_id, label="yes")
                previous_id = next_id
        else:
            # Regular process node
            node_id = f"process_{i}"
            flowchart.process(node_id, element_clean)
            flowchart.connect(previous_id, node_id)
            previous_id = node_id
    
    # Add end node
    flowchart.end("End")
    flowchart.connect(previous_id, "__end__")
    
    return flowchart


def _create_architecture_diagram(elements: list, connections: list, analysis: dict) -> ArchitectureDiagram:
    """Create an architecture diagram."""
    arch = ArchitectureDiagram()
    
    if not elements:
        # Default architecture
        arch.component("frontend", "Frontend", 100, 100, color="blue")
        arch.component("backend", "Backend", 400, 100, color="green") 
        arch.component("database", "Database", 700, 100, color="orange")
        arch.connect("frontend", "backend", "API")
        arch.connect("backend", "database", "SQL")
        return arch
    
    # Add components with grid layout
    colors = ["blue", "green", "orange", "red", "purple", "cyan", "yellow"]
    component_ids = {}
    
    # Layout components in a horizontal line or grid
    cols = min(len(elements), 4)  # Max 4 columns
    rows = (len(elements) + cols - 1) // cols  # Ceiling division
    
    for i, element in enumerate(elements):
        comp_id = element.lower().replace(" ", "_")
        component_ids[element] = comp_id
        color = colors[i % len(colors)]
        
        # Calculate position in grid
        col = i % cols
        row = i // cols
        x = 150 + col * 200  # 200px spacing between columns
        y = 100 + row * 150  # 150px spacing between rows
        
        arch.component(comp_id, element.title(), x, y, color=color)
    
    # Add connections
    for conn in connections:
        from_elem = conn.get("from", "")
        to_elem = conn.get("to", "")
        label = conn.get("label", "")
        
        from_id = component_ids.get(from_elem)
        to_id = component_ids.get(to_elem)
        
        if from_id and to_id:
            arch.connect(from_id, to_id, label)
    
    return arch


def _create_sequence_diagram(elements: list, connections: list, analysis: dict) -> SequenceDiagram:
    """Create a sequence diagram."""
    seq = SequenceDiagram()
    
    if not elements:
        # Default sequence
        seq.participant("user", "User", "blue")
        seq.participant("server", "Server", "green")
        seq.message("user", "server", "Request")
        seq.message("server", "user", "Response")
        return seq
    
    # Add participants
    colors = ["blue", "green", "orange", "red", "purple"]
    participants = {}
    
    for i, element in enumerate(elements):
        part_id = element.lower().replace(" ", "_")
        participants[element] = part_id
        color = colors[i % len(colors)]
        seq.participant(part_id, element.title(), color)
    
    # Add messages from connections
    if connections:
        for conn in connections:
            from_elem = conn.get("from", "")
            to_elem = conn.get("to", "")
            label = conn.get("label", "Message")
            
            from_id = participants.get(from_elem)
            to_id = participants.get(to_elem)
            
            if from_id and to_id:
                seq.message(from_id, to_id, label)
    else:
        # Create default message flow
        part_list = list(participants.keys())
        if len(part_list) >= 2:
            for i in range(len(part_list) - 1):
                from_id = participants[part_list[i]]
                to_id = participants[part_list[i + 1]]
                seq.message(from_id, to_id, f"Step {i + 1}")
    
    return seq


def _create_mindmap(elements: list, connections: list, analysis: dict) -> MindMap:
    """Create a mind map diagram."""
    mindmap = MindMap()
    
    if not elements:
        # Default mindmap
        mindmap.central("Central Concept", "blue")
        mindmap.branch("__central__", "Branch 1", "green")
        mindmap.branch("__central__", "Branch 2", "orange")
        return mindmap
    
    # First element as central concept
    central_label = elements[0] if elements else "Main Topic"
    mindmap.central(central_label, "blue")
    
    # Remaining elements as branches
    colors = ["green", "orange", "red", "purple", "cyan", "yellow"]
    for i, element in enumerate(elements[1:]):
        color = colors[i % len(colors)]
        mindmap.branch("__central__", element, color)
    
    return mindmap


def _create_timeline_diagram(elements: list, connections: list, analysis: dict) -> TimelineDiagram:
    """Create a timeline diagram."""
    timeline = TimelineDiagram()
    
    if not elements:
        # Default timeline
        timeline.event("2020", "Start", "Beginning", "blue")
        timeline.milestone("2021", "Milestone", "red")
        timeline.event("2022", "Progress", "Continue", "green")
        timeline.event("2023", "Current", "Today", "orange")
        timeline.build()
        return timeline
    
    # Process elements - try to extract dates
    colors = ["blue", "green", "orange", "red", "purple"]
    
    for i, element in enumerate(elements):
        color = colors[i % len(colors)]
        
        # Try to parse date:event format
        if ":" in element:
            parts = element.split(":", 1)
            if len(parts) == 2:
                date_part = parts[0].strip()
                event_part = parts[1].strip()
                
                # Check if it looks like a milestone
                if any(word in event_part.lower() for word in ["milestone", "launch", "release", "completion"]):
                    timeline.milestone(date_part, event_part, "red")
                else:
                    timeline.event(date_part, event_part, "", color)
            else:
                timeline.event(f"Event {i+1}", element, "", color)
        else:
            # No clear date, use sequence
            timeline.event(f"Step {i+1}", element, "", color)
    
    timeline.build()
    return timeline


def _create_er_diagram(elements: list, connections: list, analysis: dict) -> ERDiagram:
    """Create an ER diagram."""
    er = ERDiagram()
    
    if not elements:
        # Default ER diagram
        er.entity("user", "User", ["id", "name", "email"], "blue")
        er.entity("order", "Order", ["id", "user_id", "total"], "green")
        er.relationship("user", "order", "has", "1:N")
        return er
    
    # Add entities
    colors = ["blue", "green", "orange", "red", "purple"]
    entity_ids = {}
    
    for i, element in enumerate(elements):
        ent_id = element.lower().replace(" ", "_")
        entity_ids[element] = ent_id
        color = colors[i % len(colors)]
        
        # Basic attributes (could be enhanced with better parsing)
        attributes = ["id", "name", "created_at"]
        er.entity(ent_id, element.title(), attributes, color)
    
    # Add relationships from connections
    for conn in connections:
        from_elem = conn.get("from", "")
        to_elem = conn.get("to", "")
        label = conn.get("label", "related to")
        
        from_id = entity_ids.get(from_elem)
        to_id = entity_ids.get(to_elem)
        
        if from_id and to_id:
            er.relationship(from_id, to_id, label, "1:N")
    
    return er


def _create_simple_diagram(elements: list, connections: list, analysis: dict) -> Diagram:
    """Create a simple diagram."""
    diagram = Diagram()
    
    if not elements:
        # Very basic diagram
        box1 = diagram.box(100, 100, "Item 1", color="blue")
        box2 = diagram.box(300, 100, "Item 2", color="green")
        diagram.arrow_between(box1, box2, "connection")
        return diagram
    
    # Create boxes for elements
    colors = ["blue", "green", "orange", "red", "purple", "cyan", "yellow"]
    boxes = {}
    
    # Layout in a grid or line
    if len(elements) <= 4:
        # Horizontal layout
        for i, element in enumerate(elements):
            x = 100 + i * 200
            y = 150
            color = colors[i % len(colors)]
            box = diagram.box(x, y, element, color=color)
            boxes[element] = box
    else:
        # Grid layout
        cols = 3
        for i, element in enumerate(elements):
            x = 100 + (i % cols) * 200
            y = 100 + (i // cols) * 120
            color = colors[i % len(colors)]
            box = diagram.box(x, y, element, color=color)
            boxes[element] = box
    
    # Add connections if available
    for conn in connections:
        from_elem = conn.get("from", "")
        to_elem = conn.get("to", "")
        label = conn.get("label", "")
        
        from_box = boxes.get(from_elem)
        to_box = boxes.get(to_elem)
        
        if from_box and to_box:
            diagram.arrow_between(from_box, to_box, label)
    
    # If no connections, connect sequentially
    if not connections and len(elements) > 1:
        element_list = list(elements)
        for i in range(len(element_list) - 1):
            from_box = boxes.get(element_list[i])
            to_box = boxes.get(element_list[i + 1])
            if from_box and to_box:
                diagram.arrow_between(from_box, to_box)
    
    return diagram


def export_to_png(excalidraw_path: str, png_path: str) -> bool:
    """Export .excalidraw file to PNG using Playwright.
    
    Args:
        excalidraw_path: Path to .excalidraw file
        png_path: Output PNG path
        
    Returns:
        True if export successful, False otherwise
    """
    try:
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        export_script = script_dir / "export_playwright.js"
        
        if not export_script.exists():
            print(f"Error: export script not found at {export_script}", file=sys.stderr)
            return False
        
        # Run the export script
        cmd = ["node", str(export_script), excalidraw_path, png_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"PNG export failed: {result.stderr}", file=sys.stderr)
            return False
        
        return Path(png_path).exists()
        
    except Exception as e:
        print(f"PNG export error: {e}", file=sys.stderr)
        return False


def copy_to_obsidian(excalidraw_path: str, png_path: str) -> str:
    """Copy files to Obsidian vault diagrams directory.
    
    Args:
        excalidraw_path: Path to .excalidraw file
        png_path: Path to PNG file
        
    Returns:
        Path to copied files directory or None if failed
    """
    try:
        obsidian_env = os.environ.get("OBSIDIAN_DIAGRAMS_DIR", "")
        if not obsidian_env:
            raise SystemExit("OBSIDIAN_DIAGRAMS_DIR not set (required for --obsidian)")
        obsidian_dir = Path(os.path.expanduser(obsidian_env)).resolve()
        
        if not obsidian_dir.exists():
            print(f"Creating Obsidian diagrams directory: {obsidian_dir}")
            obsidian_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files
        excalidraw_src = Path(excalidraw_path)
        png_src = Path(png_path)
        
        excalidraw_dst = obsidian_dir / excalidraw_src.name
        png_dst = obsidian_dir / png_src.name
        
        if excalidraw_src.exists():
            import shutil
            shutil.copy2(excalidraw_src, excalidraw_dst)
        
        if png_src.exists():
            import shutil
            shutil.copy2(png_src, png_dst)
        
        return str(obsidian_dir)
        
    except Exception as e:
        print(f"Obsidian copy error: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate Excalidraw diagrams from text descriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 generate_diagram.py --text "User logs in, checks credentials, if valid show dashboard" --output /tmp/diagram
  python3 generate_diagram.py --text "Frontend calls API, API queries database" --output /tmp/arch --type architecture
  python3 generate_diagram.py --text "Timeline: 2020 start, 2021 milestone, 2022 launch" --output /tmp/timeline --obsidian
        """
    )
    
    parser.add_argument(
        "--text", 
        required=True,
        help="Text description of the diagram to generate"
    )
    
    parser.add_argument(
        "--output", 
        required=True,
        help="Output path (without extension, will add .excalidraw and .png)"
    )
    
    parser.add_argument(
        "--type",
        choices=["flowchart", "architecture", "sequence", "mindmap", "timeline", "er", "simple"],
        help="Force specific diagram type (otherwise auto-detected)"
    )
    
    parser.add_argument(
        "--obsidian",
        action="store_true",
        help="Also copy files to OBSIDIAN_DIAGRAMS_DIR (set env var to enable)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show analysis details and debug info"
    )
    
    args = parser.parse_args()
    
    try:
        # Analyze text to determine diagram type
        if args.type:
            # Force specific type
            analysis = {
                "diagram_type": args.type,
                "reasoning": f"Forced diagram type: {args.type}",
                "elements": [args.text],  # Will be parsed by specific generator
                "connections": [],
                "confidence": 1.0
            }
        else:
            # Auto-detect type
            analysis = analyze_text(args.text)
        
        if args.debug:
            print("=== Analysis Results ===", file=sys.stderr)
            print(f"Type: {analysis['diagram_type']}", file=sys.stderr)
            print(f"Confidence: {analysis['confidence']:.2f}", file=sys.stderr)
            print(f"Reasoning: {analysis['reasoning']}", file=sys.stderr)
            print(f"Elements: {analysis['elements']}", file=sys.stderr)
            print(f"Connections: {analysis['connections']}", file=sys.stderr)
            print("", file=sys.stderr)
        
        # Generate diagram
        generation_result = generate_diagram_from_analysis(analysis, args.output)
        excalidraw_path = generation_result["excalidraw_path"]
        diagram_type = generation_result["type"]
        
        # Export to PNG
        png_path = f"{args.output}.png"
        png_success = export_to_png(excalidraw_path, png_path)
        
        # Copy to Obsidian if requested
        obsidian_path = None
        if args.obsidian:
            obsidian_path = copy_to_obsidian(excalidraw_path, png_path)
        
        # Output JSON result
        result = {
            "excalidraw": excalidraw_path,
            "png": png_path if png_success else None,
            "type": diagram_type,
            "obsidian_path": obsidian_path,
            "analysis": analysis if args.debug else None
        }
        
        print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        if not Path(excalidraw_path).exists():
            sys.exit(1)
        elif not png_success:
            print(f"Warning: PNG export failed, but .excalidraw created", file=sys.stderr)
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()