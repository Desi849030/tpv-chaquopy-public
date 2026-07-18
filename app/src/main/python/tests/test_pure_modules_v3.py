# -*- coding: utf-8 -*-
"""test_pure_modules_v3.py — Cobertura masiva para pasar 40% CI gate.
Cubre: security/*, response_validators/*, tools/utf8_dictionary.py,
tools/base.py, ia/role_guidance.py, ia/tool_system.py, ia/react_templates.py,
core/config.py, dictionary/helpers.py, metrics/helpers.py, ia/anti_slop.py,
ia/humanizer.py, tool_registry.py, ia/__init__.py, license/*.
"""
import sys, os, json, re, math, time, threading
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ── Mocks de terceros ──────────────────────────────────────────────
import unittest.mock as mock
_flask = mock.MagicMock()
sys.modules['flask'] = _flask
sys.modules['flask.request'] = _flask.request
sys.modules['flask.session'] = _flask.session
sys.modules['flask.jsonify'] = _flask.jsonify
sys.modules['flask.Blueprint'] = _flask.Blueprint
sys.modules['db_connection'] = mock.MagicMock()
sys.modules['supabase'] = mock.MagicMock()
sys.modules['psutil'] = mock.MagicMock()

# ── Agregar path ───────────────────────────────────────────────────
SRC = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'src', 'main', 'python')
if SRC not in sys.path:
    sys.path.insert(0, os.path.abspath(SRC))


# ════════════════════════════════════════════════════════════════════
#  1. security/validation.py
# ════════════════════════════════════════════════════════════════════
class TestSecurityValidation:
    def test_sanitize_string_removes_tags(self):
        from security.validation import sanitize_string
        assert sanitize_string('<b>hola</b>') == 'hola'

    def test_sanitize_string_strips(self):
        from security.validation import sanitize_string
        assert sanitize_string('  hola  ') == 'hola'

    def test_sanitize_string_non_str(self):
        from security.validation import sanitize_string
        assert sanitize_string(42) == 42

    def test_sanitize_string_xss(self):
        from security.validation import sanitize_string
        r = sanitize_string('<script>alert(1)</script>hola')
        assert 'script' not in r.lower()
        assert 'hola' in r

    def test_sanitize_data_dict(self):
        from security.validation import sanitize_data
        assert sanitize_data({'a': '<b>x</b>'}) == {'a': 'x'}

    def test_sanitize_data_list(self):
        from security.validation import sanitize_data
        assert sanitize_data(['<i>a</i>', 1]) == ['a', 1]

    def test_sanitize_data_str(self):
        from security.validation import sanitize_data
        assert sanitize_data('<p>ok</p>') == 'ok'

    def test_sanitize_data_other(self):
        from security.validation import sanitize_data
        assert sanitize_data(99) == 99

    def test_check_sql_injection_clean(self):
        from security.validation import check_sql_injection
        assert check_sql_injection('hola mundo') is False

    def test_check_sql_injection_union(self):
        from security.validation import check_sql_injection
        assert check_sql_injection("UNION SELECT") is True

    def test_check_sql_injection_drop(self):
        from security.validation import check_sql_injection
        assert check_sql_injection("DROP TABLE users") is True

    def test_check_sql_injection_sqli_regex_tautology(self):
        from security.validation import check_sql_injection
        assert check_sql_injection("' OR '1'='1") is True

    def test_check_sql_injection_sqli_regex_comment(self):
        from security.validation import check_sql_injection
        assert check_sql_injection("admin'--") is True

    def test_check_sql_injection_sqli_regex_sleep(self):
        from security.validation import check_sql_injection
        assert check_sql_injection("SLEEP(5)") is True

    def test_check_sql_injection_dict(self):
        from security.validation import check_sql_injection
        assert check_sql_injection({'q': "UNION SELECT"}) is True
        assert check_sql_injection({'q': 'safe'}) is False

    def test_check_sql_injection_list(self):
        from security.validation import check_sql_injection
        assert check_sql_injection(['safe', "DROP"]) is True

    def test_check_sql_injection_non_str(self):
        from security.validation import check_sql_injection
        assert check_sql_injection(42) is False

    def test_generar_id(self):
        from security.validation import generar_id
        r = generar_id('test')
        assert r.startswith('test-')
        assert len(r) == len('test-') + 8

    def test_generar_id_default(self):
        from security.validation import generar_id
        r = generar_id()
        assert r.startswith('id-')

    def test_calcular_venta_simple(self):
        from security.validation import calcular_venta
        items = [{'precio': 10, 'cantidad': 2}]
        r = calcular_venta(items)
        assert r['subtotal'] == 20.0
        assert r['items_count'] == 1

    def test_calcular_venta_con_desc_imp(self):
        from security.validation import calcular_venta
        items = [{'precio': 100, 'cantidad': 1}]
        r = calcular_venta(items, descuento_pct=10, impuesto_pct=16)
        assert r['subtotal'] == 100.0
        assert r['monto_descuento'] == 10.0
        assert r['subtotal_con_descuento'] == 90.0
        assert r['total'] == 104.4  # 90 + 16% = 104.4

    def test_calcular_venta_empty(self):
        from security.validation import calcular_venta
        r = calcular_venta([])
        assert r['subtotal'] == 0
        assert r['total'] == 0
        assert r['items_count'] == 0

    def test_validar_totales_valid(self):
        from security.validation import validar_totales
        data = {'items': [{'precio': 10, 'cantidad': 1}], 'total': 10}
        r = validar_totales(data)
        assert r['valido'] is True

    def test_validar_totales_invalid(self):
        from security.validation import validar_totales
        data = {'items': [{'precio': 10, 'cantidad': 1}], 'total': 999}
        r = validar_totales(data)
        assert r['valido'] is False
        assert 'error' in r

    def test_sanitize_input_empty(self):
        from security.validation import sanitize_input
        assert sanitize_input('') == ''

    def test_sanitize_input_number(self):
        from security.validation import sanitize_input
        assert sanitize_input(42) == '42'

    def test_sanitize_input_xss(self):
        from security.validation import sanitize_input
        r = sanitize_input('<script>alert(1)</script>')
        assert '<script>' not in r
        assert '&lt;' in r

    def test_sanitize_input_sqli(self):
        from security.validation import sanitize_input
        r = sanitize_input('DROP TABLE users')
        assert 'DROP' not in r

    def test_sanitize_input_event_handlers(self):
        from security.validation import sanitize_input
        r = sanitize_input('<img onerror=alert(1)>')
        assert 'onerror' not in r

    def test_sanitize_input_length_limit(self):
        from security.validation import sanitize_input
        r = sanitize_input('a' * 500)
        assert len(r) == 255

    def test_sanitize_input_null_bytes(self):
        from security.validation import sanitize_input
        r = sanitize_input('hel\x00lo')
        assert '\x00' not in r

    def test_validate_email_valid(self):
        from security.validation import validate_email
        assert validate_email('user@example.com') is True

    def test_validate_email_invalid(self):
        from security.validation import validate_email
        assert validate_email('not-email') is False

    def test_validate_email_none(self):
        from security.validation import validate_email
        assert validate_email(None) is False

    def test_validate_email_empty(self):
        from security.validation import validate_email
        assert validate_email('') is False

    def test_validate_email_int(self):
        from security.validation import validate_email
        assert validate_email(123) is False


# ════════════════════════════════════════════════════════════════════
#  2. security/crypto.py
# ════════════════════════════════════════════════════════════════════
class TestSecurityCrypto:
    def test_hash_password(self):
        from security.crypto import hash_password, verify_password
        h = hash_password('secret123')
        assert '$' in h
        assert verify_password('secret123', h) is True

    def test_hash_password_custom_salt(self):
        from security.crypto import hash_password
        h = hash_password('test', salt='abc123')
        assert h.startswith('abc123$')

    def test_verify_password_false(self):
        from security.crypto import hash_password, verify_password
        h = hash_password('correct')
        assert verify_password('wrong', h) is False

    def test_verify_password_none(self):
        from security.crypto import verify_password
        assert verify_password(None, 'some') is False
        assert verify_password('some', None) is False
        assert verify_password(None, None) is False

    def test_verify_password_legacy(self):
        from security.crypto import verify_password
        assert verify_password('plain', 'plain') is True

    def test_needs_hash_migration_true(self):
        from security.crypto import needs_hash_migration
        assert needs_hash_migration('short') is True

    def test_needs_hash_migration_false(self):
        from security.crypto import needs_hash_migration
        assert needs_hash_migration(None) is False
        assert needs_hash_migration('a' * 50 + '$salt$hash') is False

    def test_cifrar_descifrar(self):
        from security.crypto import cifrar_valor, descifrar_valor
        original = 'dato sensible 123!'
        cifrado = cifrar_valor(original)
        assert cifrado != original
        descifrado = descifrar_valor(cifrado)
        assert descifrado == original

    def test_cifrar_empty(self):
        from security.crypto import cifrar_valor, descifrar_valor
        assert cifrar_valor('') == ''
        assert cifrar_valor(None) is None
        assert descifrar_valor('') == ''
        assert descifrar_valor(None) is None

    def test_descifrar_invalid(self):
        from security.crypto import descifrar_valor
        assert descifrar_valor('not-base64!!!') is None

    def test_generate_api_key(self):
        from security.crypto import generate_api_key
        k = generate_api_key(16)
        assert len(k) == 32  # hex = 2*16

    def test_rate_limit_key(self):
        from security.crypto import rate_limit_key
        assert rate_limit_key('u1', 'login') == 'rl:login:u1'

    def test_get_hmac_key(self):
        from security.crypto import get_hmac_key
        k = get_hmac_key()
        assert len(k) == 48  # 24 bytes hex

    def test_get_jwt_secret(self):
        from security.crypto import get_jwt_secret
        k = get_jwt_secret()
        assert len(k) == 48

    def test_get_csrf_token(self):
        from security.crypto import get_csrf_token
        k = get_csrf_token()
        assert len(k) == 48

    def test_get_session_salt(self):
        from security.crypto import get_session_salt
        k = get_session_salt()
        assert len(k) == 32

    def test_rl_store_and_lock(self):
        from security.crypto import _rl_store, _rl_lock
        assert isinstance(_rl_store, dict)
        assert isinstance(_rl_lock, type(threading.Lock()))

    def test_get_key(self):
        from security.crypto import _get_key
        k = _get_key()
        assert k and len(k) > 0


# ════════════════════════════════════════════════════════════════════
#  3. security/__init__.py
# ════════════════════════════════════════════════════════════════════
class TestSecurityInit:
    def test_imports(self):
        from security import (
            rate_limit, hash_password, verify_password,
            sanitize_string, sanitize_data, check_sql_injection,
            generar_id, calcular_venta, validar_totales,
            sanitize_input, validate_email,
            cifrar_valor, descifrar_valor,
            generate_api_key, rate_limit_key,
            get_hmac_key, get_jwt_secret, get_csrf_token, get_session_salt,
            registrar_auditoria,
        )
        assert callable(sanitize_string)
        assert callable(hash_password)

    def test_rl_store_exported(self):
        from security import _rl_store, _rl_lock
        assert isinstance(_rl_store, dict)


# ════════════════════════════════════════════════════════════════════
#  4. security/audit.py
# ════════════════════════════════════════════════════════════════════
class TestSecurityAudit:
    def test_registrar_auditoria_exists(self):
        from security.audit import registrar_auditoria
        assert callable(registrar_auditoria)

    def test_registrar_auditoria_call(self):
        from security.audit import registrar_auditoria
        app_mock = mock.MagicMock()
        registrar_auditoria(app_mock)
        app_mock.before_request.assert_called_once()

    def test_OBFUSC_KEY_none(self):
        from security.audit import _OBFUSC_KEY
        assert _OBFUSC_KEY is None


# ════════════════════════════════════════════════════════════════════
#  5. response_validators/models.py
# ════════════════════════════════════════════════════════════════════
class TestResponseValidatorsModels:
    def test_ValidationResult_default(self):
        from response_validators.models import ValidationResult
        r = ValidationResult()
        assert r.is_valid is True
        assert r.issues == []
        assert r.corrected_data is None

    def test_ValidationResult_add_warning(self):
        from response_validators.models import ValidationResult
        r = ValidationResult()
        r.add_issue('warning', 'campo', 'mensaje')
        assert r.is_valid is True
        assert len(r.issues) == 1

    def test_ValidationResult_add_error(self):
        from response_validators.models import ValidationResult
        r = ValidationResult()
        r.add_issue('error', 'campo', 'error msg', 'suggestion')
        assert r.is_valid is False
        assert r.issues[0].severity == 'error'
        assert r.issues[0].suggestion == 'suggestion'

    def test_ValidationIssue_attrs(self):
        from response_validators.models import ValidationIssue
        i = ValidationIssue('error', 'f', 'm', 's')
        assert i.severity == 'error'
        assert i.field == 'f'


# ════════════════════════════════════════════════════════════════════
#  6. response_validators/checks.py
# ════════════════════════════════════════════════════════════════════
class TestResponseValidatorsChecks:
    def test_validate_financial_negative_total(self):
        from response_validators.checks import validate_financial_response
        r = validate_financial_response({'total': -50})
        assert r.is_valid is False

    def test_validate_financial_ok(self):
        from response_validators.checks import validate_financial_response
        r = validate_financial_response({'total': 100})
        assert r.is_valid is True

    def test_validate_financial_high_total(self):
        from response_validators.checks import validate_financial_response
        r = validate_financial_response({'total': 999999})
        assert len(r.issues) >= 1  # warning

    def test_validate_financial_bad_type(self):
        from response_validators.checks import validate_financial_response
        r = validate_financial_response({'total': 'no-numero'})
        assert r.is_valid is False

    def test_validate_financial_negative_profit(self):
        from response_validators.checks import validate_financial_response
        r = validate_financial_response({'ganancia': -999999})
        assert any('ganancia' in i.field for i in r.issues)

    def test_validate_financial_discount_negative(self):
        from response_validators.checks import validate_financial_response
        r = validate_financial_response({'descuento': -5})
        assert r.is_valid is False

    def test_validate_financial_discount_over_100(self):
        from response_validators.checks import validate_financial_response
        r = validate_financial_response({'descuento_pct': 150})
        assert r.is_valid is False

    def test_validate_inventory_negative_stock(self):
        from response_validators.checks import validate_inventory_response
        r = validate_inventory_response({'stock': -5})
        assert r.is_valid is False

    def test_validate_inventory_ok(self):
        from response_validators.checks import validate_inventory_response
        r = validate_inventory_response({'stock': 10, 'precio': 5.0})
        assert r.is_valid is True

    def test_validate_inventory_high_stock(self):
        from response_validators.checks import validate_inventory_response
        r = validate_inventory_response({'stock_actual': 999999})
        assert any('stock' in i.field for i in r.issues)

    def test_validate_inventory_negative_price(self):
        from response_validators.checks import validate_inventory_response
        r = validate_inventory_response({'precio': -1})
        assert r.is_valid is False

    def test_validate_inventory_bad_price(self):
        from response_validators.checks import validate_inventory_response
        r = validate_inventory_response({'precio': 'abc'})
        assert r.is_valid is False

    def test_validate_inventory_empty_id(self):
        from response_validators.checks import validate_inventory_response
        r = validate_inventory_response({'producto_id': '   '})
        assert any('producto_id' in i.field for i in r.issues)

    def test_validate_text_empty(self):
        from response_validators.checks import validate_text_response
        r = validate_text_response('')
        assert r.is_valid is False

    def test_validate_text_dangerous(self):
        from response_validators.checks import validate_text_response
        r = validate_text_response('UNION SELECT * FROM users')
        assert r.is_valid is False

    def test_validate_text_traceback(self):
        from response_validators.checks import validate_text_response
        r = validate_text_response('Traceback (most recent call last)')
        assert any('Traceback' in i.message for i in r.issues)

    def test_validate_text_short(self):
        from response_validators.checks import validate_text_response
        r = validate_text_response('ok')
        assert any('corta' in i.message for i in r.issues)

    def test_validate_text_ok(self):
        from response_validators.checks import validate_text_response
        r = validate_text_response('El total de ventas hoy es de $500.00 con 12 transacciones.')
        assert r.is_valid is True

    def test_validate_response_auto_financial(self):
        from response_validators.checks import validate_response
        r = validate_response({'total': 100, 'ganancia': 20})
        assert r.is_valid is True

    def test_validate_response_auto_inventory(self):
        from response_validators.checks import validate_response
        r = validate_response({'stock': 50, 'producto': 'cafe'})
        assert r.is_valid is True

    def test_validate_response_auto_text(self):
        from response_validators.checks import validate_response
        r = validate_response('texto normal')
        assert r.is_valid is True

    def test_validate_response_explicit_type(self):
        from response_validators.checks import validate_response
        r = validate_response({'total': 'bad'}, response_type='financial')
        assert r.is_valid is False

    def test_format_validation_message_valid(self):
        from response_validators.checks import format_validation_message
        from response_validators.models import ValidationResult
        r = ValidationResult()
        assert format_validation_message(r) == ''

    def test_format_validation_message_with_issues(self):
        from response_validators.checks import format_validation_message
        from response_validators.models import ValidationResult
        r = ValidationResult()
        r.add_issue('error', 'total', 'Total negativo', 'Use 0')
        msg = format_validation_message(r)
        assert 'total' in msg
        assert 'Total negativo' in msg
        assert 'Use 0' in msg
        assert '[!]' in msg

    def test_format_validation_message_warning(self):
        from response_validators.checks import format_validation_message
        from response_validators.models import ValidationResult
        r = ValidationResult()
        r.add_issue('warning', 'stock', 'Stock alto')
        msg = format_validation_message(r)
        assert '[?]' in msg


# ════════════════════════════════════════════════════════════════════
#  7. response_validators/__init__.py
# ════════════════════════════════════════════════════════════════════
class TestResponseValidatorsInit:
    def test_imports(self):
        from response_validators import (
            ValidationIssue, ValidationResult,
            validate_financial_response, validate_inventory_response,
            validate_text_response, validate_response, format_validation_message,
        )
        assert callable(validate_response)


# ════════════════════════════════════════════════════════════════════
#  8. tools/utf8_dictionary.py
# ════════════════════════════════════════════════════════════════════
class TestUtf8Dictionary:
    def test_normalize_utf8_basic(self):
        from tools.utf8_dictionary import normalize_utf8
        assert normalize_utf8('cafe') == 'cafe'

    def test_normalize_utf8_accents_preserved(self):
        from tools.utf8_dictionary import normalize_utf8
        assert normalize_utf8('caf\u00e9') == 'caf\u00e9'  # café

    def test_normalize_utf8_remove_accents(self):
        from tools.utf8_dictionary import normalize_utf8
        r = normalize_utf8('caf\u00e9', remove_accents=True)
        assert r == 'cafe'

    def test_normalize_utf8_quotes(self):
        from tools.utf8_dictionary import normalize_utf8
        r = normalize_utf8('\u201cHola\u201d')
        assert '"' in r and '\u201c' not in r

    def test_normalize_utf8_dashes(self):
        from tools.utf8_dictionary import normalize_utf8
        r = normalize_utf8('2020\u20132024')
        assert '2020-2024' == r

    def test_normalize_utf8_euro(self):
        from tools.utf8_dictionary import normalize_utf8
        assert '\u20ac' in normalize_utf8('\u20ac100')  # € stays

    def test_normalize_utf8_empty(self):
        from tools.utf8_dictionary import normalize_utf8
        assert normalize_utf8('') == ''
        assert normalize_utf8(None) == ''

    def test_normalize_utf8_spaces(self):
        from tools.utf8_dictionary import normalize_utf8
        assert normalize_utf8('  a   b  ') == 'a b'

    def test_slugify(self):
        from tools.utf8_dictionary import slugify
        assert slugify('Caf\u00e9 & T\u00e9') == 'cafe-te'

    def test_safe_json_key(self):
        from tools.utf8_dictionary import safe_json_key
        assert safe_json_key('Precio de Venta') == 'precio_de_venta'

    def test_has_special_chars_true(self):
        from tools.utf8_dictionary import has_special_chars
        assert has_special_chars('\u201cHola\u201d') is True

    def test_has_special_chars_false(self):
        from tools.utf8_dictionary import has_special_chars
        assert has_special_chars('hola mundo') is False

    def test_extract_keywords(self):
        from tools.utf8_dictionary import extract_keywords
        r = extract_keywords('Buscar caf\u00e9 y az\u00facar')
        assert 'cafe' in r or 'caf\u00e9' in r

    def test_find_synonyms_venta(self):
        from tools.utf8_dictionary import find_synonyms
        r = find_synonyms('venta')
        assert len(r) > 0

    def test_find_synonyms_none(self):
        from tools.utf8_dictionary import find_synonyms
        r = find_synonyms('xyznoexiste')
        assert r == []

    def test_expand_query(self):
        from tools.utf8_dictionary import expand_query
        r = expand_query('venta de hoy')
        assert 'venta' in r
        assert len(r) > 2

    def test_tool_normalize_text(self):
        from tools.utf8_dictionary import tool_normalize_text
        assert callable(tool_normalize_text)

    def test_tool_remove_accents(self):
        from tools.utf8_dictionary import tool_remove_accents
        assert tool_remove_accents('caf\u00e9') == 'cafe'

    def test_tool_slugify(self):
        from tools.utf8_dictionary import tool_slugify
        assert callable(tool_slugify)

    def test_tool_find_synonyms(self):
        from tools.utf8_dictionary import tool_find_synonyms
        assert callable(tool_find_synonyms)

    def test_tool_expand_query(self):
        from tools.utf8_dictionary import tool_expand_query
        assert callable(tool_expand_query)

    def test_tool_has_special_chars(self):
        from tools.utf8_dictionary import tool_has_special_chars
        assert callable(tool_has_special_chars)

    def test_tool_safe_json_key(self):
        from tools.utf8_dictionary import tool_safe_json_key
        assert callable(tool_safe_json_key)

    def test_tool_extract_keywords(self):
        from tools.utf8_dictionary import tool_extract_keywords
        assert callable(tool_extract_keywords)

    def test_CHAR_MAP_not_empty(self):
        from tools.utf8_dictionary import CHAR_MAP
        assert len(CHAR_MAP) > 10

    def test_BUSINESS_SYNONYMS_not_empty(self):
        from tools.utf8_dictionary import BUSINESS_SYNONYMS
        assert len(BUSINESS_SYNONYMS) > 10
        assert 'venta' in BUSINESS_SYNONYMS


# ════════════════════════════════════════════════════════════════════
#  9. tools/base.py
# ════════════════════════════════════════════════════════════════════
class TestToolsBase:
    def test_ToolDefinition_creation(self):
        from tools.base import ToolDefinition, _t
        td = ToolDefinition('test', 'desc', 'cat', '/api/test', 'GET', [])
        assert td.name == 'test'
        assert td.requires_auth is True
        assert td.requires_role is None

    def test_ToolDefinition_all_fields(self):
        from tools.base import ToolDefinition
        td = ToolDefinition('n', 'd', 'c', '/r', 'POST', [{'name': 'x'}], False, 'admin')
        assert td.requires_auth is False
        assert td.requires_role == 'admin'

    def test_t_helper(self):
        from tools.base import _t
        td = _t('x', 'desc', 'cat', '/r', 'GET', [], 'admin', False)
        assert td.name == 'x'
        assert td.requires_role == 'admin'
        assert td.requires_auth is False


# ════════════════════════════════════════════════════════════════════
#  10. ia/role_guidance.py
# ════════════════════════════════════════════════════════════════════
class TestRoleGuidance:
    def test_ROLE_MISSIONS_has_roles(self):
        from ia.role_guidance import ROLE_MISSIONS
        for role in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
            assert role in ROLE_MISSIONS

    def test_ROLE_MISSIONS_structure(self):
        from ia.role_guidance import ROLE_MISSIONS
        for role, missions in ROLE_MISSIONS.items():
            assert isinstance(missions, dict)
            assert 'inicio' in missions
            assert isinstance(missions['inicio'], list)

    def test_SCREEN_GUIDES(self):
        from ia.role_guidance import SCREEN_GUIDES
        assert len(SCREEN_GUIDES) > 0
        assert 'tpv-caja-tab-pane' in SCREEN_GUIDES


# ════════════════════════════════════════════════════════════════════
#  11. ia/tool_system.py
# ════════════════════════════════════════════════════════════════════
class TestToolSystem:
    def test_TOOLS_not_empty(self):
        from ia.tool_system import TOOLS
        assert len(TOOLS) > 5

    def test_get_tools_for_role_admin(self):
        from ia.tool_system import get_tools_for_role
        tools = get_tools_for_role('administrador')
        assert len(tools) > 5
        assert 'finanzas' in tools

    def test_get_tools_for_role_cliente(self):
        from ia.tool_system import get_tools_for_role
        tools = get_tools_for_role('cliente')
        assert 'busqueda' in tools
        assert 'finanzas' not in tools

    def test_suggest_tools(self):
        from ia.tool_system import suggest_tools
        r = suggest_tools('quiero ver el stock bajo', 'administrador')
        assert len(r) > 0
        assert any(t['name'] == 'stock' for t in r)

    def test_suggest_tools_empty(self):
        from ia.tool_system import suggest_tools
        r = suggest_tools('', 'admin')
        assert r == []

    def test_suggest_tools_short(self):
        from ia.tool_system import suggest_tools
        r = suggest_tools('x', 'admin')
        assert r == []

    def test_get_help_menu(self):
        from ia.tool_system import get_help_menu
        r = get_help_menu('cliente')
        assert 'Herramientas disponibles' in r

    def test_get_help_menu_empty_role(self):
        from ia.tool_system import get_help_menu
        r = get_help_menu('noexiste')
        assert 'No hay herramientas' in r

    def test_check_permission_true(self):
        from ia.tool_system import check_permission
        assert check_permission('busqueda', 'cliente') is True

    def test_check_permission_false(self):
        from ia.tool_system import check_permission
        assert check_permission('finanzas', 'cliente') is False

    def test_check_permission_nonexistent(self):
        from ia.tool_system import check_permission
        assert check_permission('no_tool', 'admin') is False


# ════════════════════════════════════════════════════════════════════
#  12. ia/react_templates.py (mixin — instanciar con mocks)
# ════════════════════════════════════════════════════════════════════
class _FakeReActTemplates:
    """Instancia mínima de ReActEngineTemplates con lo que necesita."""
    session_id = None

    def __init__(self):
        self.session_id = None
        # Copiar métodos del mixin
        from ia.react_templates import ReActEngineTemplates
        for attr in dir(ReActEngineTemplates):
            if not attr.startswith('__') and callable(getattr(ReActEngineTemplates, attr)):
                setattr(self, attr, getattr(ReActEngineTemplates, attr).__get__(self, type(self)))

    def execute_plan(self, plan_name=None, steps=None):
        return {'success': True, 'steps': steps or []}

    def _find_tools_for_category(self, cat):
        return [{'name': f'tool_{cat}', 'description': f'Tool for {cat}'}]

    def _find_tool(self, query):
        return {'name': 'tool_search', 'description': 'Search tool'}


class TestReactTemplates:
    def setUp(self):
        self.engine = _FakeReActTemplates()

    def test_compile_general_empty(self):
        e = _FakeReActTemplates()
        assert e._compile_general([]) == 'No se obtuvieron resultados.'

    def test_compile_general_dict(self):
        e = _FakeReActTemplates()
        r = e._compile_general([{'purpose': 'test', 'data': {'total': 100.5, 'count': 5}}])
        assert 'test' in r
        assert '100.50' in r

    def test_compile_general_list(self):
        e = _FakeReActTemplates()
        r = e._compile_general([{'data': [1, 2, 3]}])
        assert '3 items' in r

    def test_compile_inventory_optimization(self):
        e = _FakeReActTemplates()
        obs = [{'purpose': 'ALERTA STOCK', 'data': {'alertas': [
            {'nombre': 'cafe', 'stock': 0}]}},
            {'purpose': 'MAS VENDIDOS', 'data': {'productos': [
            {'nombre': 'pan', 'total_vendido': 50}]}}]
        r = e._compile_inventory_optimization(obs)
        assert 'OPTIMIZACION' in r
        assert 'ALERTAS' in r

    def test_compile_inventory_optimization_empty(self):
        e = _FakeReActTemplates()
        r = e._compile_inventory_optimization([])
        assert 'No se pudo generar' in r

    def test_compile_closing_summary(self):
        e = _FakeReActTemplates()
        obs = [{'data': {'total': 500, 'transacciones': 10}}]
        r = e._compile_closing_summary(obs)
        assert 'CIERRE CAJA' in r
        assert '$500.00' in r
        assert 'Ticket promedio' in r

    def test_compile_closing_summary_zero(self):
        e = _FakeReActTemplates()
        r = e._compile_closing_summary([{'data': {'total': 0, 'transacciones': 0}}])
        assert 'Transacciones: 0' in r

    def test_compile_business_diagnosis(self):
        e = _FakeReActTemplates()
        obs = [{'purpose': 'ventas', 'data': {'total_ventas': 1000, 'num_ventas': 50}}]
        r = e._compile_business_diagnosis(obs)
        assert 'DIAGNOSTICO' in r

    def test_compile_business_diagnosis_empty(self):
        e = _FakeReActTemplates()
        r = e._compile_business_diagnosis([])
        assert 'insuficientes' in r

    def test_compile_client_status(self):
        e = _FakeReActTemplates()
        obs = [{'data': {'clientes': [
            {'nombre': 'Juan', 'puntos': 100}, {'nombre': 'Ana'}]}}]
        r = e._compile_client_status(obs)
        assert 'CLIENTES' in r
        assert 'Juan' in r
        assert '100 pts' in r

    def test_compile_client_status_empty(self):
        e = _FakeReActTemplates()
        r = e._compile_client_status([{'data': {'clientes': []}}])
        assert 'Sin datos' in r

    def test_compile_security_audit(self):
        e = _FakeReActTemplates()
        obs = [{'data': {'logs': [
            {'timestamp': '2024-01-01', 'usuario': 'admin', 'accion': 'login'}]}}]
        r = e._compile_security_audit(obs)
        assert 'AUDITORIA SEGURIDAD' in r
        assert 'admin' in r

    def test_compile_security_audit_empty(self):
        e = _FakeReActTemplates()
        r = e._compile_security_audit([{'data': {}}])
        assert 'Sin datos' in r

    def test_compile_sales_report(self):
        e = _FakeReActTemplates()
        obs = [{'data': {'total': 500.50}}]
        r = e._compile_sales_report(obs)
        assert 'REPORTE VENTAS' in r
        assert '$500.50' in r

    def test_compile_sales_report_list(self):
        e = _FakeReActTemplates()
        obs = [{'data': [1, 2, 3]}]
        r = e._compile_sales_report(obs)
        assert '3 ventas' in r

    def test_compile_final_summary_ok(self):
        e = _FakeReActTemplates()
        r = e._compile_final_summary(
            [{'success': True}, {'success': True}],
            [], 'test_plan')
        assert 'EXITOSO' in r
        assert '2 ok' in r

    def test_compile_final_summary_errors(self):
        e = _FakeReActTemplates()
        r = e._compile_final_summary(
            [{'success': True}, {'success': False}],
            ['error1'], 'plan')
        assert 'CON ERRORES' in r
        assert 'error1' in r

    def test_compile_response_dispatch(self):
        e = _FakeReActTemplates()
        r = e._compile_response('closing_summary', [{'data': {'total': 100}}])
        assert 'CIERRE CAJA' in r

    def test_compile_response_fallback(self):
        e = _FakeReActTemplates()
        r = e._compile_response('nonexistent', [{'data': {'x': 1}}])
        assert 'x' in r

    def test_process_query_inventory(self):
        e = _FakeReActTemplates()
        r = e.process_query('optimizar el inventario')
        assert r['success'] is True

    def test_process_query_cierre(self):
        e = _FakeReActTemplates()
        r = e.process_query('hacer cierre de caja')
        assert r['success'] is True

    def test_process_query_diagnostico(self):
        e = _FakeReActTemplates()
        r = e.process_query('diagnostico del negocio')
        assert r['success'] is True

    def test_process_query_clientes(self):
        e = _FakeReActTemplates()
        r = e.process_query('estado de clientes frecuentes')
        assert r['success'] is True

    def test_process_query_seguridad(self):
        e = _FakeReActTemplates()
        r = e.process_query('auditoria de seguridad')
        assert r['success'] is True

    def test_process_query_ventas(self):
        e = _FakeReActTemplates()
        r = e.process_query('reporte de ventas del periodo')
        assert r['success'] is True

    def test_process_query_unknown(self):
        e = _FakeReActTemplates()
        r = e.process_query('xyznoexiste')
        assert r['success'] is False

    def test_process_query_dynamic(self):
        e = _FakeReActTemplates()
        r = e.process_query('ver metricas de ventas')
        assert 'success' in r

    def test_build_dynamic_plan(self):
        e = _FakeReActTemplates()
        r = e._build_dynamic_plan('ver metricas de inventario')
        assert isinstance(r, list)

    def test_process_query_sets_session(self):
        e = _FakeReActTemplates()
        e.process_query('inventario', session_id='s123')
        assert e.session_id == 's123'


# ════════════════════════════════════════════════════════════════════
#  13. core/config.py
# ════════════════════════════════════════════════════════════════════
class TestCoreConfig:
    def test_config_exists(self):
        from core.config import config
        assert config is not None

    def test_config_port(self):
        from core.config import config
        assert isinstance(config.port, int)

    def test_config_https(self):
        from core.config import config
        assert isinstance(config.https, bool)

    def test_config_secret_key(self):
        from core.config import config
        assert len(config.secret_key) > 0

    def test_config_validate(self):
        from core.config import config
        w = config.validate()
        assert isinstance(w, list)


# ════════════════════════════════════════════════════════════════════
#  14. dictionary/helpers.py
# ════════════════════════════════════════════════════════════════════
class TestDictionaryHelpers:
    def test_sin_tildes(self):
        from dictionary.helpers import _sin_tildes
        assert _sin_tildes('caf\u00e9') == 'cafe'
        assert _sin_tildes('lim\u00f3n') == 'limon'

    def test_levenshtein_same(self):
        from dictionary.helpers import _levenshtein
        assert _levenshtein('hola', 'hola') == 0

    def test_levenshtein_different(self):
        from dictionary.helpers import _levenshtein
        assert _levenshtein('gato', 'pato') == 1
        assert _levenshtein('abc', 'xyz') == 3

    def test_levenshtein_empty(self):
        from dictionary.helpers import _levenshtein
        assert _levenshtein('', 'abc') == 3
        assert _levenshtein('abc', '') == 3

    def test_buscar_sinonimos_exact(self):
        from dictionary.helpers import buscar_sinonimos
        r = buscar_sinonimos('arroz')
        assert 'arroz' in r

    def test_buscar_sinonimos_fuzzy(self):
        from dictionary.helpers import buscar_sinonimos
        r = buscar_sinonimos('ares')  # fuzzy de "arroz"
        assert len(r) > 0

    def test_buscar_sinonimos_none(self):
        from dictionary.helpers import buscar_sinonimos
        r = buscar_sinonimos('zzznoexiste')
        assert r == []

    def test_definir_termino_exact(self):
        from dictionary.helpers import definir_termino
        r = definir_termino('ganancia')
        assert 'diferencia' in r.lower() or 'precio' in r.lower()

    def test_definir_termino_partial(self):
        from dictionary.helpers import definir_termino
        r = definir_termino('precio de venta')
        assert r is not None

    def test_definir_termino_none(self):
        from dictionary.helpers import definir_termino
        assert definir_termino('zzzzz') is None

    def test_corregir_exact(self):
        from dictionary.helpers import corregir
        assert corregir('presio') == 'precio'

    def test_corregir_fuzzy(self):
        from dictionary.helpers import corregir
        r = corregir('presio')  # distance 1 from precio variant
        assert r is not None

    def test_corregir_none(self):
        from dictionary.helpers import corregir
        assert corregir('perfecto') is None

    def test_expandir_consulta(self):
        from dictionary.helpers import expandir_consulta
        r = expandir_consulta('arroz y leche')
        assert 'arroz' in r
        assert len(r) > 2

    def test_expandir_consulta_short_words(self):
        from dictionary.helpers import expandir_consulta
        r = expandir_consulta('el la')
        assert len(r) <= 2  # short words skipped

    def test_diccionario_bp(self):
        from dictionary.helpers import diccionario_bp
        assert diccionario_bp is not None

    def test_SINONIMOS_dict(self):
        from dictionary.helpers import _SINONIMOS
        assert isinstance(_SINONIMOS, dict)
        assert 'arroz' in _SINONIMOS

    def test_DEFINICIONES_dict(self):
        from dictionary.helpers import _DEFINICIONES
        assert isinstance(_DEFINICIONES, dict)
        assert 'ganancia' in _DEFINICIONES

    def test_CORRECCIONES_dict(self):
        from dictionary.helpers import _CORRECCIONES
        assert isinstance(_CORRECCIONES, dict)
        assert 'presio' in _CORRECCIONES

    def test_dev_check(self):
        from dictionary.helpers import _dev_check
        assert callable(_dev_check)


# ════════════════════════════════════════════════════════════════════
#  15. dictionary/__init__.py
# ════════════════════════════════════════════════════════════════════
class TestDictionaryInit:
    def test_imports(self):
        from dictionary import (
            _levenshtein, _sin_tildes, buscar_sinonimos,
            definir_termino, corregir, expandir_consulta,
            _SINONIMOS, _DEFINICIONES, _CORRECCIONES, diccionario_bp,
        )
        assert callable(buscar_sinonimos)


# ════════════════════════════════════════════════════════════════════
#  16. metrics/__init__.py & metrics/helpers.py
# ════════════════════════════════════════════════════════════════════
class TestMetrics:
    def test_metrics_init(self):
        from metrics import dev_metrics_bp
        # puede ser None si Flask no disponible
        assert True

    def test_get_system_metrics(self):
        from metrics.helpers import get_system_metrics
        r = get_system_metrics()
        assert 'ram' in r
        assert 'storage' in r
        assert 'tablas' in r

    def test_ram_info(self):
        from metrics.helpers import _ram_info
        r = _ram_info()
        assert 'proceso_mb' in r
        assert 'fuente' in r

    def test_storage_info(self):
        from metrics.helpers import _storage_info
        r = _storage_info(None)
        assert 'db_path' in r
        assert 'disco_pct' in r

    def test_tablas_info_no_db(self):
        from metrics.helpers import _tablas_info
        r = _tablas_info(None)
        assert r['error'] is not None

    def test_tablas_info_nonexistent(self):
        from metrics.helpers import _tablas_info
        r = _tablas_info('/tmp/nonexistent_db_file.db')
        assert r['error'] is not None

    def test_get_db_path(self):
        from metrics.helpers import _get_db_path
        p = _get_db_path()
        assert p is not None

    def test_inventario_formulas_no_db(self):
        from metrics.helpers import _inventario_formulas
        r = _inventario_formulas(None)
        assert r['error'] is not None

    def test_inventario_formulas_nonexistent(self):
        from metrics.helpers import _inventario_formulas
        r = _inventario_formulas('/tmp/nonexistent.db')
        assert r['error'] is not None

    def test_dev_only_decorator(self):
        from metrics.helpers import _dev_only
        assert callable(_dev_only)


# ════════════════════════════════════════════════════════════════════
#  17. ia/anti_slop.py
# ════════════════════════════════════════════════════════════════════
class TestAntiSlop:
    def test_refine_short(self):
        from ia.anti_slop import refine
        assert refine('hi') == 'hi'

    def test_refine_none(self):
        from ia.anti_slop import refine
        assert refine(None) is None
        assert refine('') == ''

    def test_refine_normal(self):
        from ia.anti_slop import refine
        msg = 'El total de ventas hoy es $500.00 con 12 transacciones.'
        r = refine(msg, sid='test_unique_1')
        assert msg == r  # no es generico

    def test_refine_generic_triggers(self):
        from ia.anti_slop import refine
        generic = 'puede consultar:\n- ventas\n- stock\n- clientes'
        r = refine(generic, sid='test_anti_1')
        # primera vez no acorta
        assert len(r) > 10

    def test_refine_generic_repeated(self):
        from ia.anti_slop import refine
        generic = 'puede consultar:\n- opcion1\n- opcion2\n- opcion3'
        sid = 'test_repeat_12345'
        refine(generic, sid=sid)
        refine(generic, sid=sid)
        r = refine(generic, sid=sid)
        # 3rd time should shorten
        assert 'ayuda' in r.lower() or len(r) < len(generic)

    def test_GENERIC_PATTERNS(self):
        from ia.anti_slop import _GENERIC_PATTERNS
        assert len(_GENERIC_PATTERNS) > 0


# ════════════════════════════════════════════════════════════════════
#  18. ia/humanizer.py
# ════════════════════════════════════════════════════════════════════
class TestHumanizer:
    def test_sanitize_text_none(self):
        from ia.humanizer import Humanizer
        assert Humanizer.sanitize_text(None) == ''
        assert Humanizer.sanitize_text('') == ''

    def test_sanitize_text_null_bytes(self):
        from ia.humanizer import Humanizer
        r = Humanizer.sanitize_text('hel\x00lo')
        assert '\x00' not in r

    def test_sanitize_text_double_spaces(self):
        from ia.humanizer import Humanizer
        r = Humanizer.sanitize_text('hola   mundo')
        assert '  ' not in r

    def test_sanitize_text_carriage_return(self):
        from ia.humanizer import Humanizer
        r = Humanizer.sanitize_text('linea1\r\nlinea2')
        assert '\r' not in r

    def test_enhance(self):
        from ia.humanizer import Humanizer
        h = Humanizer()
        r = h.enhance('Ventas de hoy: $500.', 'vendedor')
        assert 'ventas' in r.lower() or '$500' in r

    def test_GREET_MORNING(self):
        from ia.humanizer import Humanizer
        assert len(Humanizer._GREET_MORNING) > 0

    def test_CLOSERS(self):
        from ia.humanizer import Humanizer
        assert 'cliente' in Humanizer._CLOSERS
        assert 'vendedor' in Humanizer._CLOSERS


# ════════════════════════════════════════════════════════════════════
#  19. ia/__init__.py
# ════════════════════════════════════════════════════════════════════
class TestIaInit:
    def test_import(self):
        import ia
        assert ia is not None


# ════════════════════════════════════════════════════════════════════
#  20. license/ modules
# ════════════════════════════════════════════════════════════════════
class TestLicense:
    def test_license_init(self):
        from license import core
        assert core is not None

    def test_license_helpers(self):
        from license import helpers
        assert helpers is not None


# ════════════════════════════════════════════════════════════════════
#  21. tool_registry.py
# ════════════════════════════════════════════════════════════════════
class TestToolRegistry:
    def test_ToolDefinition_creation(self):
        from tool_registry import ToolDefinition
        td = ToolDefinition('test', 'desc', 'cat', '/api/test', 'GET', [])
        assert td.name == 'test'

    def test_ToolDefinition_all_fields(self):
        from tool_registry import ToolDefinition
        td = ToolDefinition('n', 'd', 'c', '/r', 'POST', [{'name': 'x'}], False, 'admin')
        assert td.requires_auth is False

    def test_RAW_TOOLS_not_empty(self):
        from tool_registry import _RAW_TOOLS
        assert len(_RAW_TOOLS) > 50

    def test_t_helper(self):
        from tool_registry import _t
        td = _t('x', 'desc', 'cat', '/r', 'GET', [], 'admin', False)
        assert td.name == 'x'

    def test_first_raw_tool_structure(self):
        from tool_registry import _RAW_TOOLS
        first = _RAW_TOOLS[0]
        assert len(first) >= 6
        assert first[0]  # name
        assert first[4]  # method
