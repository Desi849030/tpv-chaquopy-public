import os
import unittest
import requests

BASE = "http://127.0.0.1:5000"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestFrontendSmoke(unittest.TestCase):

    def test_home_ok(self):
        r = requests.get(f"{BASE}/", timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.text) > 100)

    def test_index_exists(self):
        path = os.path.join(
            ROOT, "app", "src", "main", "assets", "frontend", "templates", "index.html"
        )
        self.assertTrue(os.path.exists(path))

    def test_css_exists(self):
        css_dir = os.path.join(
            ROOT, "app", "src", "main", "assets", "frontend", "static", "css"
        )
        self.assertTrue(os.path.isdir(css_dir))
        self.assertTrue(len(os.listdir(css_dir)) > 0)

    def test_js_exists(self):
        js_dir = os.path.join(
            ROOT, "app", "src", "main", "assets", "frontend", "static", "js"
        )
        self.assertTrue(os.path.isdir(js_dir))
        self.assertTrue(len(os.listdir(js_dir)) > 0)

    def test_home_references_static(self):
        r = requests.get(f"{BASE}/", timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertIn("/static/", r.text)

