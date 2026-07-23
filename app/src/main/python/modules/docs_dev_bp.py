"""Runtime documentation inventory for the authenticated developer role."""
from __future__ import annotations

from pathlib import Path

from flask import Blueprint, jsonify, request

from decorators import login_required, requiere_rol
from version import __version__


docs_bp = Blueprint("docs_dev", __name__)
_PYTHON_ROOT = Path(__file__).resolve().parents[1]
_REPOSITORY_ROOT = _PYTHON_ROOT.parents[3]


def _database_documents() -> list[dict]:
    from db_connection import obtener_conexion
    from documentation_loader import canonical_document_catalog

    connection = obtener_conexion()
    try:
        catalog = canonical_document_catalog(connection)
        for item in catalog:
            row = connection.execute(
                "SELECT contenido FROM documentacion WHERE nombre=?", (item["nombre"],)
            ).fetchone()
            item["preview"] = (row[0] if row else "")[:400]
        return catalog
    finally:
        connection.close()


def _source_statistics() -> dict:
    if not _REPOSITORY_ROOT.is_dir():
        return {"total_archivos": 0, "por_tipo": {}, "lineas_codigo": 0, "archivos_test": 0}
    excluded = {".git", "build", "__pycache__", ".pytest_cache", ".gradle"}
    files = [
        path for path in _REPOSITORY_ROOT.rglob("*")
        if path.is_file() and not any(part in excluded for part in path.parts)
    ]
    suffixes = ("py", "js", "css", "html", "md", "json", "sh", "yaml", "yml")
    by_type = {suffix: sum(path.suffix.lower() == f".{suffix}" for path in files) for suffix in suffixes}
    python_files = [path for path in files if path.suffix == ".py"]
    lines = 0
    for path in python_files:
        try:
            lines += len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
        except OSError:
            continue
    return {
        "total_archivos": sum(by_type.values()),
        "por_tipo": by_type,
        "lineas_codigo": lines,
        "archivos_test": sum(path.name.startswith("test_") for path in python_files),
    }


def _module_inventory() -> dict[str, list[str]]:
    result = {}
    for name in ("modules", "ia", "db", "security", "tools", "models", "license", "dictionary", "metrics"):
        directory = _PYTHON_ROOT / name
        if directory.is_dir():
            result[name] = sorted(path.name for path in directory.glob("*.py") if path.name != "__init__.py")
    return result


@docs_bp.get("/api/dev/docs/catalog")
@login_required
@requiere_rol("desarrollador")
def api_docs_catalog():
    documents = _database_documents()
    return jsonify({
        "ok": True,
        "total_documentos": len(documents),
        "total_lineas": sum(int(item.get("lineas", 0) or 0) for item in documents),
        "documentos": [
            {key: item[key] for key in ("nombre", "lineas", "actualizado")}
            for item in documents
        ],
    })


@docs_bp.get("/api/dev/docs/overview")
@login_required
@requiere_rol("desarrollador")
def api_docs_overview():
    from db_connection import obtener_conexion
    from documentation_explainer import document_overview

    query = request.args.get("name", "")
    connection = obtener_conexion()
    try:
        overview = document_overview(connection, query)
    finally:
        connection.close()
    if not overview:
        return jsonify({"ok": False, "error": "Documento no encontrado"}), 404
    return jsonify({"ok": True, "documento": overview})


@docs_bp.get("/api/dev/docs/quality")
@login_required
@requiere_rol("desarrollador")
def api_docs_quality():
    from db_connection import obtener_conexion
    from documentation_explainer import catalog_quality

    connection = obtener_conexion()
    try:
        quality = catalog_quality(connection)
    finally:
        connection.close()
    return jsonify({"ok": True, "calidad_documental": quality})


@docs_bp.route("/api/dev/docs")
@login_required
@requiere_rol("desarrollador")
def api_dev_docs():
    """Return live structure and SQLite-indexed docs without stale hardcoded counts."""
    documents = _database_documents()
    statistics = _source_statistics()
    try:
        from app import app

        endpoints = [
            {
                "ruta": rule.rule,
                "metodos": sorted(rule.methods - {"HEAD", "OPTIONS"}),
                "endpoint": rule.endpoint,
            }
            for rule in sorted(app.url_map.iter_rules(), key=lambda item: item.rule)
            if not rule.rule.startswith("/static")
        ]
        blueprints = sorted(app.blueprints)
    except Exception:
        endpoints = []
        blueprints = []

    statistics.update({
        "total_tests": "ver GitHub Actions",
        "tests_pasan": "ver GitHub Actions",
        "tests_fallan": "ver GitHub Actions",
        "cobertura_backend": "gate >= 50%; ver último CI",
        "cobertura_e2e": "ver evidencia asociada al commit",
    })
    return jsonify({
        "ok": True,
        "proyecto": f"TPV Ultra Smart v{__version__}",
        "fuente": "runtime + SQLite documentacion",
        "estadisticas": statistics,
        "modulos": _module_inventory(),
        "estructura": {
            "backend": "app/src/main/python",
            "frontend": "app/src/main/assets/frontend",
            "documentacion": "docs",
            "tests": ["tests/unit", "tests/ia", "app/src/main/python/tests"],
        },
        "endpoints": endpoints,
        "endpoints_total": len(endpoints),
        "blueprints": blueprints,
        "roles": {
            "desarrollador": {"access": ["all"], "limites_funcionales": False},
            "otros": "principio de menor privilegio",
        },
        "seguridad": {
            "password_hashing": "scrypt con compatibilidad/migración heredada",
            "rate_limiting": True,
            "sql_injection_detection": True,
            "xss_detection": True,
            "runtime_secrets": "TPV_FILES_DIR; nunca dentro del código",
            "developer_controls": "autenticación, auditoría y protección de secretos siguen activas",
        },
        "documentos": documents,
        "contenido_documentos": {item["nombre"]: item["preview"] for item in documents},
        "arreglos_recientes": [
            "documentación completa indexada para IA",
            "secretos runtime fuera del source tree",
            "frontend de navegador resuelto sin symlinks",
            "versión pública unificada",
            "suite con gate de cobertura >= 50%",
        ],
    })
