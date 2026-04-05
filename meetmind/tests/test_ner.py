"""
Tests for NER Task Extractor.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestTaskExtractor:
    """Tests for ml/ner/task_extractor.py"""

    def setup_method(self):
        from ml.ner.task_extractor import TaskExtractor
        self.extractor = TaskExtractor()

    def test_extract_returns_dict(self):
        """Extract returns all expected keys."""
        result = self.extractor.extract("Priya, please finish the slides by Wednesday.")
        assert isinstance(result, dict)
        assert "assignee" in result
        assert "deadline" in result
        assert "task_verb" in result
        assert "task_description" in result
        assert "confidence" in result

    def test_self_assignment(self):
        """'I will...' assigns to the speaker."""
        result = self.extractor.extract("I will send the report tomorrow.", speaker_name="Aditya")
        assert result["assignee"] == "Aditya"

    def test_team_assignment(self):
        """'We should...' assigns to Team."""
        result = self.extractor.extract("We should review the Q3 numbers.")
        assert result["assignee"] == "Team"

    def test_deadline_extraction(self):
        """Deadline words are detected."""
        result = self.extractor.extract("Submit the draft by Friday.")
        assert result["deadline"] is not None

    def test_action_verb_extraction(self):
        """Action verbs are detected."""
        result = self.extractor.extract("Please review the document.")
        assert result["task_verb"] == "review"
