from pathlib import Path
import tempfile
import unittest

from document_router.config import Config
from document_router.router import route_pdf


class RouterTests(unittest.TestCase):
    def config(self, root: Path) -> Config:
        return Config(
            inbox=root / "00_INBOX", projects_root=root / "01_Projekte",
            unclear_dir=root / "99_Other" / "Router_Review", log_file=root / "06_Admin" / "logs" / "router.jsonl",
            rules_file=root / "rules.toml", auto_route_threshold=0.7,
        )

    def test_routes_and_keeps_both_formats(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self.config(root)
            config.inbox.mkdir()
            project_dir = config.projects_root / "Overgrid"
            project_dir.mkdir(parents=True)
            config.log_file.parent.mkdir(parents=True)
            config.rules_file.write_text('[projects.Overgrid]\nkeywords=["nato", "protocol"]\n')
            pdf = config.inbox / "NATO_protocol.pdf"
            pdf.write_bytes(b"synthetic pdf bytes")
            result = route_pdf(pdf, config, converter=lambda _: "NATO protocol interoperability")
            self.assertEqual(result.status, "routed")
            self.assertTrue(Path(result.pdf_destination).exists())
            self.assertTrue(Path(result.markdown_destination).exists())
            self.assertEqual(Path(result.pdf_destination).parent, project_dir)
            self.assertEqual(Path(result.markdown_destination).parent, project_dir)

    def test_unknown_document_goes_to_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self.config(root)
            config.inbox.mkdir()
            config.projects_root.mkdir()
            config.log_file.parent.mkdir(parents=True)
            pdf = config.inbox / "unknown.pdf"
            pdf.write_bytes(b"synthetic pdf bytes")
            result = route_pdf(pdf, config, converter=lambda _: "unrelated document")
            self.assertEqual(result.status, "review_required")
            self.assertTrue(Path(result.pdf_destination).exists())
            self.assertEqual(Path(result.pdf_destination).parent, config.unclear_dir)
            self.assertEqual(Path(result.markdown_destination).parent, config.unclear_dir)


if __name__ == "__main__":
    unittest.main()
