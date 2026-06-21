import os, sys, json, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_PATH = os.path.join(ROOT, "app", "src", "main", "python")
if PY_PATH not in sys.path:
    sys.path.insert(0, PY_PATH)


class TestToolsFinales:
    def test_ia_tools(self):
        from tools.ia_tools import IA_TOOLS
        assert len(IA_TOOLS) > 0
        assert "ia_chat" in IA_TOOLS

    def test_validacion_tools(self):
        from tools.validacion_tools import VALIDACION_TOOLS
        assert len(VALIDACION_TOOLS) > 0

    def test_utf8_dictionary_import(self):
        import tools.utf8_dictionary
        assert hasattr(tools.utf8_dictionary, 'CHAR_MAP')
        assert len(tools.utf8_dictionary.CHAR_MAP) > 0

    def test_utf8_normalize(self):
        from tools.utf8_dictionary import normalize_utf8
        result = normalize_utf8("Hola “Mundo”")
        assert '\u201c' not in result
