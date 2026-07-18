from __future__ import annotations

import importlib.util
import math
import struct
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "live_3dgs_validation.py"


def load_module():
    name = "comfycolab_3dgs_live_validation_test"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def minimal_ply(path: Path, *, opacity: float = 1.0) -> None:
    names = (
        "x", "y", "z", "f_dc_0", "f_dc_1", "f_dc_2", "opacity",
        "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3",
    )
    header = [
        "ply",
        "format binary_little_endian 1.0",
        "element vertex 2",
        *(f"property float {name}" for name in names),
        "end_header",
        "",
    ]
    row = [0.0] * len(names)
    row[names.index("opacity")] = opacity
    path.write_bytes(
        "\n".join(header).encode("ascii")
        + struct.pack(f"<{len(row)}f", *row)
        + struct.pack(f"<{len(row)}f", *row)
    )


class Live3DGSValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_prompt_wires_file3d_output_to_preview_and_save(self) -> None:
        prompt = self.module.build_prompt("input/example.png", seed=123)
        self.assertEqual(
            prompt["2"]["class_type"],
            "ComfyColabTripoSplatImageToGaussianSplat",
        )
        self.assertEqual(prompt["90"]["inputs"]["model_file"], ["2", 1])
        self.assertEqual(prompt["91"]["inputs"]["mesh"], ["2", 1])
        self.assertEqual(prompt["2"]["inputs"]["output_format"], "ply")

    def test_binary_ply_validation_and_live_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.ply"
            minimal_ply(path)
            artifact = self.module.inspect_3dgs_ply(path)
        self.assertEqual(artifact["gaussianCount"], 2)
        self.assertTrue(artifact["plyValidated"])
        record = self.module.validation_record(
            artifact,
            runtime_seconds=1.25,
            peak_vram_bytes=4096,
        )
        self.assertEqual(record["status"], "passed")
        self.assertEqual(record["benchmark"]["gaussianCount"], 2)

    def test_invalid_ply_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.ply"
            minimal_ply(path, opacity=math.nan)
            with self.assertRaisesRegex(ValueError, "non-finite"):
                self.module.inspect_3dgs_ply(path)


if __name__ == "__main__":
    unittest.main()
