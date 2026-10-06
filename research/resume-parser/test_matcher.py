import unittest

from matcher import build_suggestions, compare_skills, extract_skills


class MatcherTests(unittest.TestCase):
    def test_extracts_aliases_without_matching_partial_words(self):
        self.assertEqual(extract_skills("Built with Python and PostgreSQL."), {"Python", "PostgreSQL"})
        self.assertNotIn("Go", extract_skills("I am going to build it"))

    def test_compares_job_and_resume_skills(self):
        result = compare_skills(
            "Python, SQL, and AWS experience",
            "Looking for Python, AWS, Docker, and Kubernetes",
        )
        self.assertEqual(result["matched"], {"Python", "AWS"})
        self.assertEqual(result["missing"], {"Docker", "Kubernetes"})
        self.assertEqual(result["additional"], {"SQL"})

    def test_suggestions_are_grounded_in_gaps(self):
        gaps = {"matched": {"Python"}, "missing": {"Docker", "AWS"}}
        suggestions = build_suggestions(gaps, 0.6)
        self.assertTrue(any("AWS, Docker" in suggestion for suggestion in suggestions))
        self.assertTrue(any("Python" in suggestion for suggestion in suggestions))
        self.assertTrue(any("measurable outcomes" in suggestion for suggestion in suggestions))


if __name__ == "__main__":
    unittest.main()
