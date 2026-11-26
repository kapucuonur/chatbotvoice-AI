"""The data deletion pages Facebook Login requires must render (they returned 500: templates were missing)."""
import os
import sys

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402


def test_data_deletion_pages_render():
    client = app.test_client()
    for path, text in (("/data-deletion-instructions", "How to delete your data"),
                       ("/data-deletion-status", "Data deletion status")):
        r = client.get(path)
        assert r.status_code == 200, path
        body = r.get_data(as_text=True)
        assert text in body and "info@trihonor.com" in body
