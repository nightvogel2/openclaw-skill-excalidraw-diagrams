#!/usr/bin/env python3
"""
Export & Deliver — takes an .excalidraw file, exports to PNG, copies to destinations, cleans up.

Usage:
    python3 export_and_deliver.py --input diagram.excalidraw [--obsidian] [--name my_diagram] [--cleanup /tmp/script.py]
    
Outputs JSON with paths to all artifacts.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
EXPORT_SCRIPT = SCRIPT_DIR / "export_playwright.js"
# Optional: set OBSIDIAN_DIAGRAMS_DIR to enable vault copies.
# Example: export OBSIDIAN_DIAGRAMS_DIR=~/Documents/Obsidian/diagrams
OBSIDIAN_DIAGRAMS = os.environ.get("OBSIDIAN_DIAGRAMS_DIR", "")
VALIDATOR_SCRIPT = SCRIPT_DIR / "line_routing_validator.py"


def validate(excalidraw_path: str) -> dict:
    """Run line routing validator on the diagram. Returns issues dict."""
    try:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR_SCRIPT), excalidraw_path],
            capture_output=True, text=True, timeout=30
        )
        return {"stdout": result.stdout, "returncode": result.returncode}
    except Exception as e:
        return {"error": str(e)}


def export_png(excalidraw_path: str, png_path: str) -> bool:
    """Export .excalidraw to PNG via Playwright."""
    try:
        result = subprocess.run(
            ["node", str(EXPORT_SCRIPT), excalidraw_path, png_path],
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0 and os.path.exists(png_path)
    except Exception as e:
        print(f"PNG export failed: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Export and deliver Excalidraw diagrams")
    parser.add_argument("--input", required=True, help="Path to .excalidraw file")
    parser.add_argument("--obsidian", action="store_true", help="Copy to Obsidian vault")
    parser.add_argument("--name", help="Output name (without extension). Defaults to input filename.")
    parser.add_argument("--cleanup", nargs="*", help="Files to delete on success (e.g. temp Python scripts)")
    parser.add_argument("--output-dir", help="Custom output directory (default: same as input)")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(json.dumps({"error": f"Input file not found: {input_path}"}))
        sys.exit(1)

    name = args.name or input_path.stem
    output_dir = Path(args.output_dir) if args.output_dir else input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    excalidraw_final = output_dir / f"{name}.excalidraw"
    png_path = output_dir / f"{name}.png"

    # If input is in /tmp and output_dir is different, copy
    if input_path != excalidraw_final:
        shutil.copy2(input_path, excalidraw_final)

    # Validate
    validation = validate(str(excalidraw_final))

    # Export PNG
    png_ok = export_png(str(excalidraw_final), str(png_path))

    result = {
        "excalidraw": str(excalidraw_final),
        "png": str(png_path) if png_ok else None,
        "validation": validation.get("returncode", -1) == 0,
    }

    # Copy to Obsidian (optional)
    if args.obsidian:
        if not OBSIDIAN_DIAGRAMS:
            result["obsidian_error"] = "OBSIDIAN_DIAGRAMS_DIR not set"
        else:
            obsidian_dir = Path(os.path.expanduser(OBSIDIAN_DIAGRAMS)).resolve()
            obsidian_dir.mkdir(parents=True, exist_ok=True)
            obs_excalidraw = obsidian_dir / f"{name}.excalidraw"
            shutil.copy2(excalidraw_final, obs_excalidraw)
            result["obsidian_excalidraw"] = str(obs_excalidraw)
            if png_ok:
                obs_png = obsidian_dir / f"{name}.png"
                shutil.copy2(png_path, obs_png)
                result["obsidian_png"] = str(obs_png)

    # Cleanup temp files on success
    if args.cleanup and png_ok:
        for f in args.cleanup:
            try:
                os.remove(f)
            except OSError:
                pass
        # Also clean /tmp input if it was there
        if str(input_path).startswith("/tmp/") and input_path != excalidraw_final:
            try:
                os.remove(input_path)
            except OSError:
                pass

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
