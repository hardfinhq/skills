# Copyright (c) 2026 - Present. Hardfin, Inc. All rights reserved.
"""Exercise release checks against isolated copies with fictional values."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
VERSION = "4.5.6"
FIELDS = (
    ("plugin.json", ("version",)),
    (".claude-plugin/plugin.json", ("version",)),
    (".claude-plugin/marketplace.json", ("plugins", 0, "version")),
    (".cursor-plugin/marketplace.json", ("plugins", 0, "version")),
    ("mcp.json", ("mcpServers", "hardfin", "headers", "X-Hardfin-Skills")),
    (".mcp.json", ("mcpServers", "hardfin", "headers", "X-Hardfin-Skills")),
)


class ReleaseTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        names = [name for name, _ in FIELDS]
        names += ["hardfin-skills.json", "release/cli-surface.json", "scripts/check_release.py"]
        for name in names:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        for name, fields in FIELDS:
            self.set_value(name, fields, VERSION)
        self.set_value("hardfin-skills.json", ("version",), VERSION)
        (self.root / "release/cli-surface.json").write_text('{"commands": ["sample"]}\n')
        self.skill = self.root / "skills/sample-skill/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text("---\nname: sample-skill\ndescription: Sample records\n---\n")

    def set_value(self, name, fields, value):
        path = self.root / name
        data = json.loads(path.read_text())
        target = data
        for field in fields[:-1]:
            target = target[field]
        target[fields[-1]] = value
        path.write_text(json.dumps(data, indent=4) + "\n")

    def run_check(self, *arguments):
        return subprocess.run(
            [sys.executable, "-I", str(self.root / "scripts/check_release.py"), *arguments],
            cwd=self.root, text=True, capture_output=True, check=False,
        )

    def assert_rejected(self, result, *details):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        for detail in details:
            self.assertIn(detail, result.stderr)

    def test_passing_tree(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Release checks passed", result.stdout)

    def test_matching_tag(self):
        result = self.run_check("--tag", "v" + VERSION)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_mismatched_tag(self):
        self.assert_rejected(self.run_check("--tag", "v4.5.7"), "tag", "v4.5.7", "v" + VERSION)

    def test_tag_requires_prefix(self):
        self.assert_rejected(self.run_check("--tag", VERSION), "tag", "v" + VERSION)

    def test_marker_version_mismatch(self):
        self.set_value("hardfin-skills.json", ("version",), "4.5.7")
        result = self.run_check()
        self.assert_rejected(result, VERSION, "4.5.7", *(name for name, _ in FIELDS))

    def test_invalid_marker_version(self):
        self.set_value("hardfin-skills.json", ("version",), None)
        self.assert_rejected(self.run_check(), "hardfin-skills.json", "None")

    def test_skill_name_mismatch(self):
        self.skill.write_text("---\nname: other-skill\n---\n")
        self.assert_rejected(self.run_check(), "skills/sample-skill/SKILL.md", "other-skill", "sample-skill")

    def test_skill_name_missing(self):
        self.skill.write_text("---\ndescription: Sample records\n---\n")
        self.assert_rejected(self.run_check(), "skills/sample-skill/SKILL.md", "None")

    def test_surface_missing(self):
        (self.root / "release/cli-surface.json").unlink()
        self.assert_rejected(self.run_check(), "release/cli-surface.json")

    def test_surface_invalid_json(self):
        (self.root / "release/cli-surface.json").write_text("{")
        self.assert_rejected(self.run_check(), "release/cli-surface.json")


def mismatch_test(name, fields):
    def test(self):
        self.set_value(name, fields, "7.8.9")
        self.assert_rejected(self.run_check(), name, "7.8.9", VERSION)
    return test


for index, (name, fields) in enumerate(FIELDS):
    setattr(ReleaseTest, f"test_version_mismatch_{index + 1}", mismatch_test(name, fields))


if __name__ == "__main__":
    unittest.main()
