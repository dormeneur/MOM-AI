"""
Tests for the API and pipeline service.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestDatabase:
    """Tests for database models and setup."""

    def test_init_db(self):
        """Database initialises without errors."""
        from api.database import init_db
        init_db()  # Should not raise

    def test_create_session(self):
        """Can create a session in the database."""
        from api.database import SessionLocal, Session, init_db, generate_uuid
        init_db()
        db = SessionLocal()
        try:
            session = Session(
                id=generate_uuid(),
                meet_url="https://meet.google.com/test",
                status="pending",
            )
            db.add(session)
            db.commit()

            found = db.query(Session).filter(Session.id == session.id).first()
            assert found is not None
            assert found.meet_url == "https://meet.google.com/test"
        finally:
            db.close()


class TestFastAPI:
    """Tests for FastAPI app startup."""

    def test_app_imports(self):
        """FastAPI app imports without errors."""
        from api.main import app
        assert app is not None
        assert app.title == "MeetMind API"

    def test_health_endpoint(self):
        """Health endpoint returns ok."""
        from fastapi.testclient import TestClient
        from api.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_create_session_endpoint(self):
        """POST /api/sessions creates a session."""
        from fastapi.testclient import TestClient
        from api.main import app
        client = TestClient(app)
        response = client.post("/api/sessions", json={
            "meet_url": "https://meet.google.com/abc-defg-hij",
            "host_email": "test@test.com",
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "pending"
