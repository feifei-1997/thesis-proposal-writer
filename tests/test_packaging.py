import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_release_archive_is_linux_compatible_and_secret_free(self):
        with tempfile.TemporaryDirectory() as output_dir:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "package_skill.py"),
                    "--root",
                    str(SKILL_ROOT),
                    "--output-dir",
                    output_dir,
                ],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            archive_path = Path(result["artifact"])
            self.assertTrue(archive_path.is_file())
            self.assertTrue(Path(result["hash_file"]).is_file())

            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
                self.assertIn("core/cqvip_client.py", names)
                self.assertFalse(any("\\" in name for name in names))
                self.assertNotIn("README.md", names)
                client_source = archive.read("core/cqvip_client.py").decode("utf-8")
                self.assertNotRegex(
                    client_source,
                    r"(?m)^\s*CQVIP_API_KEY\s*=\s*['\"][^'\"]+",
                )


if __name__ == "__main__":
    unittest.main()
