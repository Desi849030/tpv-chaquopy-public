import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestFrontendAssets(unittest.TestCase):

    def test_main_css_files(self):
        css_base = os.path.join(ROOT, "app", "src", "main", "assets", "frontend", "static", "css")
        expected = [
            "modulo_0.css",
            "modulo_1.css",
            "modulo_2.css",
            "modulo_3.css",
            "tpv-ux.css",
            "tpv_theme.css",
            "tpv_modals.css",
        ]
        for name in expected:
            self.assertTrue(os.path.exists(os.path.join(css_base, name)), name)

    def test_main_js_files(self):
        js_base = os.path.join(ROOT, "app", "src", "main", "assets", "frontend", "static", "js")
        expected = [
            "tpv_api.js",
            "tpv_chat.js",
            "tpv_ventas.js",
            "tpv_seguridad.js",
            "tpv_i18n.js",
        ]
        for name in expected:
            self.assertTrue(os.path.exists(os.path.join(js_base, name)), name)

