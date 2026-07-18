#!/usr/bin/env python3
"""Build the 3DGS smoke prompt and validate its binary PLY artifact."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Any


MODEL_REVISION = "VAST-AI/TripoSplat@de3b99ab2627d565a8d5fc40f2db52557b82b974"
SCHEMA = "comfycolab-3dgs-live-validation-v1"
SCALAR_TYPES = {
    "char": ("b", 1),
    "int8": ("b", 1),
    "uchar": ("B", 1),
    "uint8": ("B", 1),
    "short": ("h", 2),
    "int16": ("h", 2),
    "ushort": ("H", 2),
    "uint16": ("H", 2),
    "int": ("i", 4),
    "int32": ("i", 4),
    "uint": ("I", 4),
    "uint32": ("I", 4),
    "float": ("f", 4),
    "float32": ("f", 4),
    "double": ("d", 8),
    "float64": ("d", 8),
}
REQUIRED_GROUPS = {
    "position": ("x", "y", "z"),
    "dc": ("f_dc_0", "f_dc_1", "f_dc_2"),
    "opacity": ("opacity",),
    "scale": ("scale_0", "scale_1", "scale_2"),
    "rotation": ("rot_0", "rot_1", "rot_2", "rot_3"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_prompt(
    image_name: str,
    *,
    seed: int = 0,
    quality: str = "Fast — 65K",
    output_format: str = "ply",
) -> dict[str, Any]:
    if output_format != "ply":
        raise ValueError("The release-gate validator requires PLY output")
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "2": {
            "class_type": "ComfyColabTripoSplatImageToGaussianSplat",
            "inputs": {
                "image": ["1", 0],
                "quality": quality,
                "seed": int(seed),
                "remove_background": True,
                "sampling_steps": 20,
                "guidance_scale": 3.0,
                "enable_sampling_preview": True,
                "output_format": output_format,
            },
        },
        "90": {"class_type": "Preview3D", "inputs": {"model_file": ["2", 1]}},
        "91": {
            "class_type": "SaveGLB",
            "inputs": {
                "mesh": ["2", 1],
                "filename_prefix": "3dgs/validation/triposplat-fast-65k",
            },
        },
    }


def inspect_3dgs_ply(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    if not payload:
        raise ValueError("PLY artifact is empty")
    marker = b"end_header\n"
    header_end = payload.find(marker)
    if header_end < 0:
        raise ValueError("PLY header is missing end_header")
    header_end += len(marker)
    header = payload[:header_end].decode("ascii", "strict").splitlines()
    if len(header) < 3 or header[0] != "ply":
        raise ValueError("PLY header is invalid")
    if header[1] != "format binary_little_endian 1.0":
        raise ValueError("PLY must be binary_little_endian 1.0")

    vertex_count: int | None = None
    properties: list[tuple[str, str]] = []
    current_element: str | None = None
    for line in header[2:]:
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "element":
            current_element = parts[1] if len(parts) > 1 else None
            if current_element == "vertex":
                if len(parts) != 3:
                    raise ValueError("PLY vertex element is malformed")
                vertex_count = int(parts[2])
        elif parts[0] == "property" and current_element == "vertex":
            if len(parts) != 3 or parts[1] == "list":
                raise ValueError("PLY vertex properties must be scalar")
            if parts[1] not in SCALAR_TYPES:
                raise ValueError(f"Unsupported PLY type: {parts[1]}")
            properties.append((parts[1], parts[2]))
    if vertex_count is None or vertex_count <= 0:
        raise ValueError("PLY vertex count must be positive")

    names = [name for _kind, name in properties]
    missing = {
        group: [name for name in required if name not in names]
        for group, required in REQUIRED_GROUPS.items()
    }
    missing = {group: names for group, names in missing.items() if names}
    if missing:
        raise ValueError(f"PLY lacks required 3DGS properties: {missing}")

    row_bytes = sum(SCALAR_TYPES[kind][1] for kind, _name in properties)
    if len(payload) < header_end + vertex_count * row_bytes:
        raise ValueError("PLY vertex payload is truncated")
    offset = header_end
    first_vertex: dict[str, float] = {}
    for kind, name in properties:
        code, width = SCALAR_TYPES[kind]
        first_vertex[name] = float(struct.unpack_from("<" + code, payload, offset)[0])
        offset += width
    for name in ("x", "y", "z", "opacity"):
        if not math.isfinite(first_vertex[name]):
            raise ValueError(f"PLY property {name} has a non-finite value")

    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "format": "binary_little_endian",
        "artifactKind": "3dgs-ply",
        "gaussianCount": vertex_count,
        "properties": names,
        "plyValidated": True,
        "file3dValidated": True,
        "modelRevision": MODEL_REVISION,
    }


def validation_record(
    artifact: dict[str, Any],
    *,
    runtime_seconds: float | None = None,
    peak_vram_bytes: int | None = None,
) -> dict[str, Any]:
    metrics_complete = (
        runtime_seconds is not None
        and runtime_seconds > 0
        and peak_vram_bytes is not None
        and peak_vram_bytes > 0
    )
    status = "passed" if metrics_complete else "artifact-validated"
    return {
        "schema": SCHEMA,
        "status": status,
        "completedAt": dt.datetime.now(dt.timezone.utc).isoformat() if metrics_complete else None,
        "sources": {
            "triposplatModel": MODEL_REVISION,
        },
        "gate": {
            "name": "triposplat_fast_65k_file3d_ply",
            "status": status,
            "evidence": f"sha256:{artifact['sha256']}",
        },
        "benchmark": {
            "quality": "Fast — 65K",
            "gaussianCount": artifact["gaussianCount"],
            "runtimeSeconds": runtime_seconds,
            "peakVramBytes": peak_vram_bytes,
            "plyBytes": artifact["bytes"],
            "plySha256": artifact["sha256"],
            "plyValidated": True,
            "file3dValidated": True,
            "outputFormat": "ply",
        },
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    prompt = subparsers.add_parser("prompt")
    prompt.add_argument("--image-name", required=True)
    prompt.add_argument("--seed", type=int, default=0)
    prompt.add_argument("--output", type=Path)
    inspect = subparsers.add_parser("inspect")
    inspect.add_argument("artifact", type=Path)
    inspect.add_argument("--runtime-seconds", type=float)
    inspect.add_argument("--peak-vram-bytes", type=int)
    inspect.add_argument("--record", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "prompt":
        payload = build_prompt(args.image_name, seed=args.seed)
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    artifact = inspect_3dgs_ply(args.artifact)
    record = validation_record(
        artifact,
        runtime_seconds=args.runtime_seconds,
        peak_vram_bytes=args.peak_vram_bytes,
    )
    text = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if args.record:
        args.record.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
