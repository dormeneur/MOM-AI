"""
Tests for MOM Generator.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mom.generator import MOMGenerator


class TestMOMGenerator:
    """Tests for mom/generator.py"""

    def setup_method(self):
        self.gen = MOMGenerator()

    def test_global_mom_has_sections(self):
        """Global MOM contains all required sections."""
        html = self.gen.generate_global(
            summary="This is a test summary.",
            decisions=[{"speaker": "A", "text": "We decided X"}],
            topics=[{"speaker": "B", "text": "Topic Y"}],
            action_items=[{
                "task_description": "Do Z",
                "assigned_to_name": "A",
                "assigned_by_name": "B",
                "deadline": "Friday",
                "confidence": 0.9,
            }],
            participants=[{"display_name": "A", "email": "a@test.com"}],
        )
        assert "Executive Summary" in html
        assert "Key Topics" in html
        assert "Decisions Made" in html
        assert "Action Items" in html
        assert "Unresolved" in html
        assert "MeetMind" in html

    def test_personalised_mom_greeting(self):
        """Personalised MOM has correct greeting."""
        html = self.gen.generate_personalised(
            participant={"display_name": "Priya Singh", "email": "priya@co.com"},
            summary="Summary here.",
            decisions=[],
            topics=[],
            tasks=[{"task_description": "Finish slides", "deadline": "Wed"}],
        )
        assert "Hi Priya" in html
        assert "YOUR Action Items" in html
        assert "Finish slides" in html

    def test_empty_action_items(self):
        """MOM handles empty action items gracefully."""
        html = self.gen.generate_global(
            summary="Nothing happened.",
            decisions=[],
            topics=[],
            action_items=[],
        )
        assert "No action items recorded" in html
