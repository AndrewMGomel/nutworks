from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.validate_package import MIT_LICENSE, PackageValidationError, validate_package


ROOT = Path(__file__).resolve().parents[1]
CONTENT_CASES = json.loads(
    (Path(__file__).parent / "fixtures" / "package" / "content-cases.json").read_text(
        encoding="utf-8"
    )
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_valid_repo(root: Path) -> list[str]:
    plugin = root / "plugins" / "nutworks"
    files = [
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        "LICENSE",
        "THIRD_PARTY_NOTICES.md",
        "references/unused.md",
        "runtime-files.json",
        "skills/nuts/SKILL.md",
        "skills/nuts/references/plan.md",
        "third_party/compound-engineering/LICENSE",
        "third_party/compound-engineering/provenance.json",
    ]
    manifest = {
        "name": "nutworks",
        "version": "0.1.0",
        "description": "NUTS test package",
        "author": {"name": "Andrew Gomel"},
        "license": "MIT",
        "keywords": ["workflow"],
    }
    codex_manifest = {
        **manifest,
        "skills": "./skills/",
        "interface": {
            "displayName": "Nutworks",
            "shortDescription": "Run NUTS",
            "longDescription": "Run the NUTS workflow.",
            "developerName": "Andrew Gomel",
            "category": "Coding",
            "capabilities": ["Read", "Write"],
            "defaultPrompt": ["Use NUTS"],
        },
    }
    write_json(plugin / ".codex-plugin" / "plugin.json", codex_manifest)
    write_json(plugin / ".claude-plugin" / "plugin.json", manifest)
    write_json(
        root / ".agents" / "plugins" / "marketplace.json",
        {
            "name": "nutworks",
            "interface": {"displayName": "Nutworks"},
            "plugins": [
                {
                    "name": "nutworks",
                    "source": {"source": "local", "path": "./plugins/nutworks"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "Coding",
                }
            ],
        },
    )
    write_json(
        root / ".claude-plugin" / "marketplace.json",
        {
            "name": "nutworks",
            "owner": {"name": "Andrew Gomel"},
            "metadata": {"description": "Nutworks", "version": "0.1.0"},
            "plugins": [
                {
                    "name": "nutworks",
                    "description": "NUTS test package",
                    "author": {"name": "Andrew Gomel"},
                    "source": "./plugins/nutworks",
                }
            ],
        },
    )
    (root / "LICENSE").write_text(MIT_LICENSE, encoding="utf-8")
    (plugin / "LICENSE").write_text(MIT_LICENSE, encoding="utf-8")
    (plugin / "THIRD_PARTY_NOTICES.md").write_text(
        "# Third-party notices\n\nCompound Engineering, Copyright (c) 2025 Every. MIT.\n",
        encoding="utf-8",
    )
    ce_license = plugin / "third_party" / "compound-engineering" / "LICENSE"
    ce_license.parent.mkdir(parents=True, exist_ok=True)
    ce_license.write_text(
        MIT_LICENSE.replace("Copyright (c) 2026 Andrew Gomel", "Copyright (c) 2025 Every"),
        encoding="utf-8",
    )
    write_json(
        plugin / "third_party" / "compound-engineering" / "provenance.json",
        {
            "upstream": {
                "repository": "https://github.com/EveryInc/compound-engineering",
                "commit": "a" * 40,
                "license_path": "third_party/compound-engineering/LICENSE",
            },
            "adapted": [{"destination": "skills/nuts/references/plan.md"}],
        },
    )
    skill = plugin / "skills" / "nuts" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(
        "---\nname: nuts\ndescription: Run NUTS.\n---\n\n# NUTS\n\nRead "
        "[the Plan protocol](references/plan.md).\n",
        encoding="utf-8",
    )
    (skill.parent / "references" / "plan.md").parent.mkdir(parents=True, exist_ok=True)
    (skill.parent / "references" / "plan.md").write_text("# Plan\n", encoding="utf-8")
    (plugin / "references").mkdir(parents=True, exist_ok=True)
    (plugin / "references" / "unused.md").write_text("# Allowed but not linked\n", encoding="utf-8")
    write_json(plugin / "runtime-files.json", {"schema_version": 1, "files": sorted(files)})
    return sorted(files)


class PackageValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        build_valid_repo(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def assert_invalid(self, expected: str) -> None:
        with self.assertRaises(PackageValidationError) as caught:
            validate_package(self.root)
        self.assertIn(expected, "\n".join(caught.exception.errors))

    def allowlist(self) -> dict[str, object]:
        return json.loads(
            (self.root / "plugins/nutworks/runtime-files.json").read_text(encoding="utf-8")
        )

    def write_allowlist(self, payload: dict[str, object]) -> None:
        write_json(self.root / "plugins/nutworks/runtime-files.json", payload)

    def test_clean_package_has_repeatable_bounded_inventory(self) -> None:
        first = validate_package(self.root)
        second = validate_package(self.root)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "passed")
        self.assertEqual(first["claim"], "source-and-stage-validation-only")
        self.assertNotIn("sha256", json.dumps(first))

    def test_undeclared_and_missing_files_are_rejected(self) -> None:
        extra = self.root / "plugins/nutworks/extra.md"
        extra.write_text("extra\n", encoding="utf-8")
        self.assert_invalid("runtime files not declared")
        extra.unlink()
        payload = self.allowlist()
        files = list(payload["files"])
        files.append("missing.md")
        payload["files"] = sorted(files)
        self.write_allowlist(payload)
        self.assert_invalid("allowlisted runtime files are missing")

    def test_link_is_rejected_without_following_it(self) -> None:
        target = self.root / "outside.txt"
        target.write_text("outside\n", encoding="utf-8")
        os.symlink(target, self.root / "plugins/nutworks/link.md")
        self.assert_invalid("link is forbidden")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is unavailable")
    def test_special_file_is_rejected(self) -> None:
        os.mkfifo(self.root / "plugins/nutworks/pipe")
        self.assert_invalid("special file is forbidden")

    def test_private_content_and_secret_patterns_are_rejected(self) -> None:
        skill = self.root / "plugins/nutworks/skills/nuts/SKILL.md"
        for value in CONTENT_CASES["private"] + CONTENT_CASES["secrets"]:
            with self.subTest(value=value):
                original = skill.read_text(encoding="utf-8")
                skill.write_text(original + value + "\n", encoding="utf-8")
                with self.assertRaises(PackageValidationError):
                    validate_package(self.root)
                skill.write_text(original, encoding="utf-8")

    def test_allowed_content_does_not_trigger_private_or_secret_scan(self) -> None:
        skill = self.root / "plugins/nutworks/skills/nuts/SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8") + "\n".join(CONTENT_CASES["allowed"]),
            encoding="utf-8",
        )
        self.assertEqual(validate_package(self.root)["status"], "passed")

    def test_broken_reference_is_rejected(self) -> None:
        skill = self.root / "plugins/nutworks/skills/nuts/SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8") + "\n[Missing](references/missing.md)\n",
            encoding="utf-8",
        )
        self.assert_invalid("broken or undeclared reference")

    def test_broken_provenance_destination_is_rejected(self) -> None:
        provenance_path = (
            self.root / "plugins/nutworks/third_party/compound-engineering/provenance.json"
        )
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        provenance["adapted"][0]["destination"] = "skills/nuts/references/missing.md"
        write_json(provenance_path, provenance)
        self.assert_invalid("broken or undeclared reference")

    def test_development_fixture_path_is_rejected_even_when_declared(self) -> None:
        fixture = self.root / "plugins/nutworks/tests/fixtures/run.json"
        fixture.parent.mkdir(parents=True)
        fixture.write_text("{}\n", encoding="utf-8")
        payload = self.allowlist()
        payload["files"] = sorted([*payload["files"], "tests/fixtures/run.json"])
        self.write_allowlist(payload)
        self.assert_invalid("development-only runtime path")

    def test_manifest_and_catalog_divergence_are_rejected(self) -> None:
        manifest_path = self.root / "plugins/nutworks/.claude-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["version"] = "0.2.0"
        write_json(manifest_path, manifest)
        self.assert_invalid("host manifests disagree on version")
        manifest["version"] = "0.1.0"
        write_json(manifest_path, manifest)
        catalog_path = self.root / ".claude-plugin/marketplace.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog["plugins"][0]["source"] = str(self.root / "plugins/nutworks")
        write_json(catalog_path, catalog)
        self.assert_invalid("exact relative source")

    def test_traversal_and_duplicate_allowlist_entries_are_rejected(self) -> None:
        payload = self.allowlist()
        payload["files"] = [*payload["files"], "../outside", payload["files"][0]]
        self.write_allowlist(payload)
        self.assert_invalid("unsafe path")
        self.assert_invalid("duplicate paths")

    def test_license_mismatch_and_merged_notice_are_rejected(self) -> None:
        plugin_license = self.root / "plugins/nutworks/LICENSE"
        plugin_license.write_text(MIT_LICENSE + "Copyright (c) 2025 Every\n", encoding="utf-8")
        self.assert_invalid("exact approved MIT text")

    def test_duplicate_json_keys_are_rejected(self) -> None:
        manifest = self.root / "plugins/nutworks/.claude-plugin/plugin.json"
        manifest.write_text('{"name":"nutworks","name":"other"}\n', encoding="utf-8")
        self.assert_invalid("duplicate JSON key")

    def test_source_catalog_link_is_rejected(self) -> None:
        catalog = self.root / ".agents/plugins/marketplace.json"
        saved = catalog.read_text(encoding="utf-8")
        catalog.unlink()
        replacement = self.root / "catalog.json"
        replacement.write_text(saved, encoding="utf-8")
        os.symlink(replacement, catalog)
        self.assert_invalid("must be a regular non-link file")

    def test_linked_catalog_parent_is_rejected(self) -> None:
        agents = self.root / ".agents"
        moved = self.root / "catalog-parent"
        agents.rename(moved)
        os.symlink(moved, agents)
        self.assert_invalid("linked package/catalog path component is forbidden")


class CurrentRepositoryPackageTest(unittest.TestCase):
    def test_current_repository_package(self) -> None:
        self.assertEqual(validate_package(ROOT)["status"], "passed")

    def test_public_pilot_identity_and_install_commands(self) -> None:
        repository = "https://github.com/AndrewMGomel/nutworks"
        codex = json.loads(
            (ROOT / "plugins/nutworks/.codex-plugin/plugin.json").read_text(
                encoding="utf-8"
            )
        )
        claude = json.loads(
            (ROOT / "plugins/nutworks/.claude-plugin/plugin.json").read_text(
                encoding="utf-8"
            )
        )
        for manifest in (codex, claude):
            self.assertEqual(manifest["homepage"], repository)
            self.assertEqual(manifest["repository"], repository)
            self.assertEqual(manifest["author"]["url"], "https://github.com/AndrewMGomel")
        self.assertEqual(codex["interface"]["websiteURL"], repository)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "codex plugin marketplace add AndrewMGomel/nutworks --ref v0.1.0",
            readme,
        )
        self.assertIn(
            "claude plugin marketplace add AndrewMGomel/nutworks@v0.1.0 --scope user",
            readme,
        )
        self.assertIn(f"{repository}/issues", readme)
        self.assertIn("pilot-unqualified", readme)


if __name__ == "__main__":
    unittest.main()
