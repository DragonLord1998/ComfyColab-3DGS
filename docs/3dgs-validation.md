# ComfyColab 3DGS validation

Local checks prove the preserved node graph, pinned download metadata, workflow
contract, native ComfyUI capability declaration, and structural PLY validation.
They do not prove live inference.

The stable-release live gate is:

1. start the pinned ComfyUI revision with only the `3dgs` pack;
2. run `ComfyColabTripoSplatImageToGaussianSplat` at `Fast — 65K`;
3. save the facade's `FILE_3D` output as PLY;
4. validate a non-zero binary little-endian artifact with required position,
   DC color, opacity, scale, and rotation properties;
5. record Gaussian count, bytes, SHA-256, runtime, and peak VRAM in
   `3dgs-validation.json`.

`scripts/live_3dgs_validation.py` builds the exact prompt and validates the
result artifact. The record remains pending until those real-runtime metrics
are supplied.
