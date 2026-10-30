"""Run with python3 -m unittest discover -s tests. Uses disposable repositories."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import re
from urllib.parse import unquote, urlsplit

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/bootstrap_repo.py"
CORE = {"docs/ai/current-task.md", "docs/ai/project-context.md", "docs/ai/architecture-guardrails.md"}
PLAN = "docs/plan/current-todo.md"
DEEP = {"docs/context/repo-map.md", "docs/prd/current-prd.md", "docs/architecture/current-architecture.md", "docs/qa/current-qa-checklist.md"}


class BootstrapBehavior(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="coding-env-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "项目 with spaces"
        self.root.mkdir()

    def run_cli(self, *args, success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.root), *args], capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_default_is_minimal_and_has_no_code_side_effects(self):
        self.run_cli()
        self.assertEqual(set(self.snapshot()), CORE)
        self.assertFalse((self.root / "src").exists())
        self.assertFalse((self.root / "AGENTS.md").exists())

    def test_guided_and_expanded_have_expected_artifacts_and_resolved_templates(self):
        self.run_cli("--preset", "guided")
        self.assertEqual(set(self.snapshot()), CORE | {PLAN})
        self.run_cli("--preset", "expanded")
        self.assertEqual(set(self.snapshot()), CORE | {PLAN} | DEEP)
        for content in self.snapshot().values():
            self.assertNotIn(b"{{", content)

    def test_rerun_preserves_user_documents_and_uncommitted_source(self):
        self.run_cli("--preset", "expanded")
        task = self.root / "docs/ai/current-task.md"
        task.write_text("已授权交付；用户自行补充，不能覆盖。")
        (self.root / "main.py").write_text("user_work = True")
        before = self.snapshot()
        self.run_cli("--preset", "expanded")
        self.assertEqual(self.snapshot(), before)

    def test_existing_domain_documents_are_reused(self):
        for category in ("prd", "architecture"):
            path = self.root / "docs" / category / "existing.md"
            path.parent.mkdir(parents=True)
            path.write_text("existing source")
        self.run_cli("--preset", "expanded")
        self.assertFalse((self.root / "docs/prd/current-prd.md").exists())
        self.assertFalse((self.root / "docs/architecture/current-architecture.md").exists())
        self.assertEqual((self.root / "docs/prd/existing.md").read_text(), "existing source")

    def test_greenfield_can_opt_in_to_code_layout(self):
        self.run_cli("--mode", "greenfield", "--code-layout", "layered")
        for path in ("src/modules", "src/shared", "src/workflows", "src/contracts", "tests", "scripts"):
            self.assertTrue((self.root / path).is_dir())

    def test_unknown_existing_code_is_not_treated_as_greenfield(self):
        (self.root / "main.go").write_text("package main")
        before = self.snapshot()
        self.run_cli("--mode", "greenfield", "--code-layout", "layered", success=False)
        self.assertEqual(self.snapshot(), before)
        result = self.run_cli()
        self.assertIn("Mode: existing", result.stdout)
        self.assertFalse((self.root / "src").exists())


class SkillPackageReferences(unittest.TestCase):
    def test_published_document_file_links_resolve(self):
        """Check inline local file links; template destinations exist downstream."""
        root = SCRIPT.parents[1]
        missing = []
        for doc in root.rglob("*.md"):
            if any(part in {".git", "assets"} for part in doc.relative_to(root).parts):
                continue
            text = re.sub(r"```.*?```", "", doc.read_text(), flags=re.S)
            for target in re.findall(r"\]\(([^)]+)\)", text):
                target = urlsplit(target)
                if target.scheme or target.netloc or not target.path:
                    continue
                path = (doc.parent / unquote(target.path)).resolve()
                if not path.exists():
                    missing.append(f"{doc.relative_to(root)} -> {target.path}")
        self.assertEqual([], missing, "Broken local file links: " + "; ".join(missing))


if __name__ == "__main__":
    unittest.main()
