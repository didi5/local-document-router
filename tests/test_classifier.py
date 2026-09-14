from pathlib import Path
import tempfile
import unittest

from document_router.classifier import classify_rules, project_names


class ClassifierTests(unittest.TestCase):
    def test_routes_solaegis_document(self):
        decision = classify_rules(
            "Haertel_2024.pdf", "MACE cardiovascular hospital costs and DRG analysis",
            ["SolAegis", "Overgrid"], {"SolAegis": ["mace", "drg"], "Overgrid": ["nato"]},
        )
        self.assertEqual(decision.project, "SolAegis")
        self.assertGreaterEqual(decision.confidence, 0.7)

    def test_marks_close_matches_ambiguous(self):
        decision = classify_rules(
            "report.pdf", "shared protocol study",
            ["Alpha", "Beta"], {"Alpha": ["shared"], "Beta": ["protocol"]},
        )
        self.assertIsNone(decision.project)
        self.assertIn("ambiguous", decision.reason)

    def test_discovers_new_project_without_code_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Brand_New_Project").mkdir()
            self.assertEqual(project_names(root), ["Brand_New_Project"])


if __name__ == "__main__":
    unittest.main()
