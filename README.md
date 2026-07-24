# ComfyColab 3DGS

`ComfyColab-3DGS` owns Gaussian-splat generation, splat output formats, model
artifacts, workflows, tests, and validation records for ComfyColab.

The first release preserves the legacy ComfyUI target directory
`ComfyColab-Triposplat`, the public node ID
`ComfyColabTripoSplatImageToGaussianSplat`, its current
`ComfyColab/3D` category, schema, and workflow filename. A category rename is a
separate compatibility change.

## Development status

The current version is `0.1.0-dev.0`. It is an extraction pre-release and
does not claim stable packaging or completed live GPU validation.

The facade produces a native `SPLAT` and a splat `FILE_3D` in PLY, SPZ, or
KSPLAT form. It requires the native TripoSplat and Gaussian-splat nodes in the
pinned ComfyUI revision. Core enforces the manifest's authenticated post-clone
symbol probes. `runtime/doctor.py` repeats that capability check when its
structured context includes `comfyui_root`; standalone local runs report it as
unchecked rather than making an unsupported claim.

Pinned Hugging Face artifacts use authenticated `huggingface_hub` with
high-performance Xet first. Public repositories retry anonymously when a saved
token is stale, then retain the existing resumable HTTP downloader as a
compatibility fallback.

## Validation tiers

Local validation is the required first tier:

```bash
PYTHON=/path/to/python3 bash scripts/check.sh
```

Local checks validate the node graph, downloads, workflow, manifest, native
capability declaration, and binary PLY inspector.

Live validation is a separate Colab/GPU tier. A real run must load the pinned
native ComfyUI capability, execute the workflow, and produce a non-empty splat
that passes `scripts/live_3dgs_validation.py`. That release gate is not implied
by a local pass.
