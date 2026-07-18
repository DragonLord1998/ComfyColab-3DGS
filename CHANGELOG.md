# Changelog

All notable changes to ComfyColab 3DGS are recorded here. Development versions
remain pre-release until their native ComfyUI and live GPU gates are complete.

## Unreleased

- Pending: execute the pinned native TripoSplat workflow on Colab/GPU and
  publish a non-empty, structurally valid splat record.
- Pending: verify cold and cached model provisioning through modular core.

## 0.1.0-dev.0 - 2026-07-18

### Added

- Extracted the TripoSplat facade while preserving its public node ID, schema,
  category, workflow filename, and `ComfyColab-Triposplat` target directory.
- Declared the pinned native ComfyUI symbols and checksum-bound model assets.
- Added offline lifecycle hooks, a binary PLY validator, local tests, notices,
  and the standalone pack manifest.

### Validation

- Local graph, workflow, download, manifest, and binary-format tests are
  available through `scripts/check.sh`.
- Native GPU inference and produced-splat quality remain a separate live gate.
