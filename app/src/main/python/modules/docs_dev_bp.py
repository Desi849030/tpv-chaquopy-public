"""Blueprint: Documentación completa del sistema para desarrollador"""
from flask import Blueprint, jsonify
from decorators import login_required, requiere_rol
import os, sys, json

docs_bp = Blueprint('docs_dev', __name__)

@docs_bp.route('/api/dev/docs')
@login_required
@requiere_rol('desarrollador')
def _leer_docs_de_bd():
    """Lee todos los documentos desde SQLite"""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        rows = conn.execute("SELECT nombre, contenido FROM documentacion ORDER BY nombre").fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}
    except:
        return {}

def api_dev_docs():
    """Documentación completa: estructura, tests, cobertura, endpoints, módulos"""
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
    PY_PATH = os.path.join(ROOT, 'app', 'src', 'main', 'python')
    
    # Contar archivos por tipo
    counts = {}
    for ext in ['py', 'js', 'css', 'html', 'md', 'json', 'sh']:
        counts[ext] = sum(1 for _ in os.popen(f'find {ROOT} -name "*.{ext}" -not -path "*/.git/*" -not -path "*/__pycache__/*" -not -path "*/tpv-review/*" 2>/dev/null').read().splitlines())
    
    # Módulos Python
    modulos = {}
    for root_dir in ['modules', 'ia', 'db', 'security', 'sync', 'tools', 'models', 'license', 'dictionary', 'metrics']:
        p = os.path.join(PY_PATH, root_dir)
        if os.path.isdir(p):
            modulos[root_dir] = [f for f in os.listdir(p) if f.endswith('.py') and f != '__init__.py']
    
    # Endpoints
    endpoints = []
    try:
        from app import app
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
            if not rule.rule.startswith('/static'):
                endpoints.append({
                    "ruta": rule.rule,
                    "metodos": sorted(rule.methods - {'HEAD', 'OPTIONS'}),
                    "endpoint": rule.endpoint
                })
    except:
        pass
    
    # Estructura de directorios
    estructura = {}
    for d in ['app/src/main/python', 'tests', 'docs', 'tools', 'scripts']:
        path = os.path.join(ROOT, d)
        if os.path.isdir(path):
            estructura[d] = [f for f in os.listdir(path) if not f.startswith('.') and not f.startswith('__')]
    
    return jsonify({
        "ok": True,
        "proyecto": "TPV Ultra Smart v8.14.0",
        "fecha": "2026-06-21",
        "estadisticas": {
            "total_archivos": sum(counts.values()),
            "por_tipo": counts,
            "total_tests": 510,
            "tests_pasan": 505,
            "tests_fallan": 1,
            "cobertura_backend": "48%",
            "cobertura_e2e": "100%",
            "lineas_codigo": 9833
        },
        "modulos": modulos,
        "estructura": estructura,
        "endpoints": endpoints,
        "endpoints_total": len(endpoints),
        "blueprints": [
            "auth_bp", "ventas_bp", "ventas_core_bp", "catalogo_bp",
            "inv_bp", "admin_bp", "agent_bp", "agent_chat_bp",
            "metrics_bp", "tienda_bp", "ai_bp", "settings_bp",
            "loyalty_bp", "assistant_bp", "diag_bp", "tools_bp",
            "reportes_bp", "debug_sync_bp", "telecom_bp", "publico_bp",
            "usuarios_bp", "clientes_bp", "i18n_bp", "sec_bp",
            "proactive_bp", "ai_routes_bp", "tests_info_bp", "docs_bp"
        ],
        "roles": ["desarrollador", "administrador", "supervisor", "vendedor", "cajero", "cliente"],
        "seguridad": {
            "hash": "SHA-256 + salt",
            "rate_limiting": "si",
            "sql_injection_detection": "si",
            "xss_detection": "si",
            "https_hsts": "activar con export TPV_HTTPS=1",
            "bio_auth": "HMAC SHA-256"
        },
        
        "contenido_documentos": {
            "README.md": open(os.path.join(ROOT, 'README.md')).read()[:2000] if os.path.exists(os.path.join(ROOT, 'README.md')) else '',
            "CHANGELOG.md": open(os.path.join(ROOT, 'CHANGELOG.md')).read()[:2000] if os.path.exists(os.path.join(ROOT, 'CHANGELOG.md')) else '',
            "LICENSE": open(os.path.join(ROOT, 'LICENSE')).read()[:500] if os.path.exists(os.path.join(ROOT, 'LICENSE')) else '',
            "docs/API_REFERENCE.md": open(os.path.join(ROOT, 'docs/API_REFERENCE.md')).read()[:3000] if os.path.exists(os.path.join(ROOT, 'docs/API_REFERENCE.md')) else '',
            "docs/ARCHITECTURE.md": open(os.path.join(ROOT, 'docs/ARCHITECTURE.md')).read()[:2000] if os.path.exists(os.path.join(ROOT, 'docs/ARCHITECTURE.md')) else '',
            "docs/BACKEND_MAP.md": open(os.path.join(ROOT, 'docs/BACKEND_MAP.md')).read()[:2000] if os.path.exists(os.path.join(ROOT, 'docs/BACKEND_MAP.md')) else '',
            "docs/DATABASE_SCHEMA.md": open(os.path.join(ROOT, 'docs/DATABASE_SCHEMA.md')).read()[:2000] if os.path.exists(os.path.join(ROOT, 'docs/DATABASE_SCHEMA.md')) else '',
            "docs/DOCUMENTACION_TESIS.md": open(os.path.join(ROOT, 'docs/DOCUMENTACION_TESIS.md')).read()[:3000] if os.path.exists(os.path.join(ROOT, 'docs/DOCUMENTACION_TESIS.md')) else '',
            "docs/CONTRIBUTING.md": open(os.path.join(ROOT, 'docs/CONTRIBUTING.md')).read()[:1500] if os.path.exists(os.path.join(ROOT, 'docs/CONTRIBUTING.md')) else '',
            "docs/CHECKLIST_RELEASE.md": open(os.path.join(ROOT, 'docs/CHECKLIST_RELEASE.md')).read()[:1000] if os.path.exists(os.path.join(ROOT, 'docs/CHECKLIST_RELEASE.md')) else '',
            "requirements.txt": open(os.path.join(ROOT, 'requirements.txt')).read() if os.path.exists(os.path.join(ROOT, 'requirements.txt')) else '',
        },
        "arreglos_recientes": [
            "response_validators/checks.py: _MAX_REASONABLE_SALE definido",
            "ventas_reportes.py: movido a legacy",
            "_head.html: partial sin DOCTYPE",
            "HTTPS/HSTS implementado",
            "JS obsoleto app_4-8.js eliminado",
            "CSS inline documentado",
            "backup/restore automático de BD post-tests"
        ]
    })
