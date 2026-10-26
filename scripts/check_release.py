# Copyright (c) 2026 - Present. Hardfin, Inc. All rights reserved.
"""Check release versions, skill names and the recorded CLI surface."""

import argparse
import json
from pathlib import Path
import re
import sys


def check(root, tag=None):
    errors = []

    def read_json(name):
        try:
            return json.loads((root / name).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            errors.append(f"{name}: {error}")
            return None

    marker = read_json("hardfin-skills.json")
    version = marker.get("version") if isinstance(marker, dict) else None
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        errors.append(f"hardfin-skills.json: version={version!r}; expected X.Y.Z")

    def compare(name, field, value):
        if value != version or version is None:
            errors.append(f"{name}: {field}={value!r}; expected {version!r}")

    for name in ("plugin.json", ".claude-plugin/plugin.json"):
        data = read_json(name)
        compare(name, "version", data.get("version") if isinstance(data, dict) else None)

    for name in (".claude-plugin/marketplace.json", ".cursor-plugin/marketplace.json"):
        data = read_json(name)
        plugins = data.get("plugins", []) if isinstance(data, dict) else []
        entries = [entry for entry in plugins if isinstance(entry, dict) and entry.get("name") == "hardfin"] if isinstance(plugins, list) else []
        if len(entries) != 1:
            errors.append(f"{name}: expected one hardfin entry; found {len(entries)}")
        compare(name, "hardfin.version", entries[0].get("version") if len(entries) == 1 else None)

    for name in ("mcp.json", ".mcp.json"):
        data = read_json(name)
        value = None
        try:
            value = data["mcpServers"]["hardfin"]["headers"]["X-Hardfin-Skills"]
        except (KeyError, TypeError):
            pass
        compare(name, "X-Hardfin-Skills", value)

    if tag is not None and tag != f"v{version}":
        errors.append(f"tag: {tag!r}; expected 'v{version}'")

    for path in sorted((root / "skills").glob("*/SKILL.md")):
        source = path.read_text(encoding="utf-8")
        lines = source.splitlines()
        value = None
        if lines and lines[0] == "---" and "---" in lines[1:]:
            frontmatter = lines[1:lines.index("---", 1)]
            for line in frontmatter:
                match = re.fullmatch(r"name:\s*(.*?)\s*", line)
                if match:
                    value = match[1].strip("\"'")
                    break
        if value != path.parent.name:
            errors.append(f"{path.relative_to(root)}: name={value!r}; expected {path.parent.name!r}")

    read_json("release/cli-surface.json")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Release tag, including its v prefix")
    args = parser.parse_args()
    errors = check(Path(__file__).resolve().parent.parent, args.tag)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Release checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
