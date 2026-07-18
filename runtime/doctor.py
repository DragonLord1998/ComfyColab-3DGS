#!/usr/bin/env python3
"""Offline structural and native-capability doctor for the 3DGS pack."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_NODE_ID = "ComfyColabTripoSplatImageToGaussianSplat"
REQUIRED_NATIVE = {
    "comfy_extras/nodes_triposplat.py": (
        "TripoSplatPreprocessImage",
        "TripoSplatConditioning",
        "TripoSplatSamplingPreview",
        "VAEDecodeTripoSplat",
    ),
    "comfy_extras/nodes_gaussian_splat.py": (
        "SplatToFile3D",
        "RenderSplat",
    ),
}


def doctor(comfyui_root: Path | None = None) -> dict[str, object]:
    node_file = ROOT / "custom_nodes" / "ComfyColab-Triposplat" / "nodes.py"
    missing_paths = [] if node_file.is_file() else [str(node_file.relative_to(ROOT))]
    missing_symbols: dict[str, list[str]] = {}
    capability_status = "unchecked"
    if comfyui_root is not None:
        capability_status = "ok"
        for relative, symbols in REQUIRED_NATIVE.items():
            path = comfyui_root / relative
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
            missing = [symbol for symbol in symbols if symbol not in text]
            if missing:
                missing_symbols[relative] = missing
        if missing_symbols:
            capability_status = "error"
    source = node_file.read_text(encoding="utf-8") if node_file.is_file() else ""
    missing_nodes = [] if f'"{PUBLIC_NODE_ID}"' in source else [PUBLIC_NODE_ID]
    status = "ok" if not missing_paths and not missing_nodes and not missing_symbols else "error"
    return {
        "schema": 1,
        "pack": "3dgs",
        "status": status,
        "public_node_ids": [PUBLIC_NODE_ID],
        "native_capability_status": capability_status,
        "missing_paths": missing_paths,
        "missing_node_ids": missing_nodes,
        "missing_native_symbols": missing_symbols,
        "network_used": False,
        "writes": [],
    }


def main() -> int:
    raw_context = sys.stdin.read()
    context = json.loads(raw_context) if raw_context.strip() else {}
    comfyui_root = context.get("comfyui_root")
    result = doctor(Path(comfyui_root) if comfyui_root else None)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
