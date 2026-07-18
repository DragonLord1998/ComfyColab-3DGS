from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_NODE_ID = "ComfyColabTripoSplatImageToGaussianSplat"


class PackContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(
            (ROOT / "comfycolab-pack.json").read_text(encoding="utf-8")
        )

    def test_identity_and_legacy_node_root_are_stable(self) -> None:
        self.assertEqual(self.manifest["schema"], 1)
        self.assertEqual(self.manifest["id"], "3dgs")
        self.assertEqual(
            self.manifest["node_roots"],
            [{
                "source": "custom_nodes/ComfyColab-Triposplat",
                "target": "ComfyColab-Triposplat",
            }],
        )
        self.assertEqual(self.manifest["health_checks"]["node_ids"], [PUBLIC_NODE_ID])

    def test_release_hygiene_is_explicitly_prerelease(self) -> None:
        version = self.manifest["version"]
        self.assertRegex(version, r"^\d+\.\d+\.\d+-dev\.\d+$")
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn(f'version = "{version}"', project)
        self.assertTrue((ROOT / "CHANGELOG.md").is_file())
        self.assertTrue((ROOT / "CONTRIBUTING.md").is_file())

    def test_model_revision_and_artifact_integrity_are_immutable(self) -> None:
        dependency = self.manifest["dependencies"][0]
        self.assertRegex(dependency["ref"], re.compile(r"^[0-9a-f]{40}$"))
        self.assertEqual(dependency["install_phase"], "lazy")
        self.assertEqual(len(dependency["artifacts"]), 5)
        for artifact in dependency["artifacts"]:
            self.assertGreater(artifact["bytes"], 0)
            self.assertRegex(artifact["sha256"], re.compile(r"^[0-9a-f]{64}$"))

    def test_native_comfyui_capability_is_declarative(self) -> None:
        self.assertNotIn("probes", self.manifest["compatibility"]["comfyui"])
        probes = [
            probe
            for probe in self.manifest["probes"]
            if probe["phase"] == "post_clone"
        ]
        self.assertEqual(
            {probe["path"] for probe in probes},
            {
                "comfy_extras/nodes_triposplat.py",
                "comfy_extras/nodes_gaussian_splat.py",
            },
        )
        self.assertTrue(
            all(
                probe["type"] == "file_symbols"
                and probe["target"] == "comfyui"
                and probe["symbols"]
                for probe in probes
            )
        )
        self.assertEqual(
            [
                probe
                for probe in self.manifest["probes"]
                if probe["phase"] == "post_start"
            ],
            [{
                "phase": "post_start",
                "type": "comfy_node_ids",
                "values": [PUBLIC_NODE_ID],
            }],
        )

    def test_hooks_and_workflow_exist(self) -> None:
        for hook in self.manifest["hooks"].values():
            self.assertEqual(hook["network"], "none")
            self.assertTrue((ROOT / hook["path"]).is_file())
        for workflow in self.manifest["workflows"]:
            payload = json.loads((ROOT / workflow).read_text(encoding="utf-8"))
            self.assertIn(PUBLIC_NODE_ID, {node["type"] for node in payload["nodes"]})


if __name__ == "__main__":
    unittest.main()
