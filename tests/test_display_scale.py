import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "display-scale.py"
spec = importlib.util.spec_from_file_location("display_scale", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DisplayScaleRotationTests(unittest.TestCase):
    def test_scale_preserves_manually_rotated_monitor(self):
        for angle in (0, 1, 2, 3):
            with self.subTest(angle=angle):
                monitor = {"name": "eDP-1", "width": 2880, "height": 1800,
                           "refreshRate": 120, "x": 0, "y": 0, "transform": angle}
                with patch.object(module, "hypr_env", return_value={}), patch.object(
                    module, "current_monitor", return_value=monitor
                ), patch.object(module.subprocess, "run") as run:
                    module.apply_live("eDP-1", "1.5")
                cmd = run.call_args.args[0]
                self.assertEqual(cmd[0:2], ["hyprctl", "eval"])
                self.assertIn(f"transform = {angle}", cmd[2])
                self.assertIn("scale = 1.5", cmd[2])

    def test_missing_transform_defaults_to_zero(self):
        monitor = {"width": 2880, "height": 1800, "refreshRate": 120, "x": 0, "y": 0}
        with patch.object(module, "hypr_env", return_value={}), patch.object(
            module, "current_monitor", return_value=monitor
        ), patch.object(module.subprocess, "run") as run:
            module.apply_live("eDP-1", "1.5")
        self.assertIn("transform = 0", run.call_args.args[0][2])


if __name__ == "__main__":
    unittest.main()
