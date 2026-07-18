# Contributing to ComfyColab 3DGS

## Scope

This repository owns Gaussian-splat generation, model artifacts, splat output
contracts, its ComfyUI facade, workflows, and 3DGS validation. Mesh generation
and refinement belong in ComfyColab 3D; generic Colab orchestration belongs in
ComfyColab core.

Preserve `ComfyColabTripoSplatImageToGaussianSplat` and the legacy
`ComfyColab-Triposplat` target directory unless a separately reviewed
compatibility migration explicitly changes them.

## Local validation

Run:

```bash
PYTHON=/path/to/python3 bash scripts/check.sh
```

The local suite proves graph construction, download integrity, workflow wiring,
manifest declarations, offline doctor behavior, and binary PLY inspection. It
does not prove that the pinned native nodes load on Colab or that GPU inference
produces a useful splat.

## Live validation

Changes to native-symbol requirements, model assets, graph wiring, output
formats, or GPU behavior require a pinned Colab/GPU run with
`scripts/live_3dgs_validation.py`. Record the resulting artifact metadata and
report local and live outcomes independently.

## Pull-request checklist

- Manifest and project versions match.
- Model revisions, file sizes, and checksums remain immutable.
- Native ComfyUI symbol probes remain declarative.
- Public node and workflow compatibility is preserved or documented.
- `scripts/check.sh` passes.
- Changelog and third-party notices are current.
