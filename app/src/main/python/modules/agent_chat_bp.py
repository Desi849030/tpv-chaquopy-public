# -*- coding: utf-8 -*-
"""Blueprint: Agente IA chat + status (v8.0 definitivo)."""

from flask import Blueprint, request, jsonify, session, current_app
import os
from datetime import datetime

from anon_identity import ensure_anon_client_id, ensure_request_id, identity_payload

agent_chat_bp = Blueprint('agent_chat', __name__)

_agent = None
_agent_loaded = False
try:
    from ia.agent_master import agent as _agent
    _agent_loaded = True
except Exception as e:
    print(f"⚠️ Agente IA no disponible: {e}")


def _saludo_inteligente(rol, name):
    """Saludo contextual por rol. Por seguridad, nunca revela el rol interno
    ni usa frases que puedan ser confundidas con escalado de privilegios.
    El agente se presenta como asistente del negocio."""
    h = datetime.now().hour
    t = "Buenos días" if h < 12 else "Buenas tardes" if h < 19 else "Buenas noches"
    icon = '👋'
    n = name or rol

    # Saludos neutros por rol — sin filtrar info sensible del sistema
    if rol == 'cliente':
        return f"{t} {icon} ¡Bienvenido a la tienda! Soy tu asistente virtual. Puedo ayudarte a buscar productos, ver precios, ofertas y disponibilidad. ¿Qué necesitas?"
    elif rol == 'vendedor':
        return f"{t} {icon} Hola {n}, soy tu copiloto de ventas. Pregúntame por tus ventas de hoy, stock, precios o productos más vendidos."
    elif rol == 'administrador':
        return f"{t} {icon} Hola Admin {n}, tengo el negocio bajo control. Pídeme balance, gastos, rendimiento del personal o inventario."
    elif rol == 'desarrollador':
        return f"{t} {icon} Hola {n}, panel de desarrollador activo. Telemetría del sistema, integridad de BD, logs y métricas listas."
    elif rol == 'supervisor':
        return f"{t} {icon} Hola {n}, panel de supervisión activo. Dashboard, análisis ABC, rotación y predicciones."
    elif rol == 'cajero':
        return f"{t} {icon} Hola {n}, estoy listo para ayudarte con la caja. Pregúntame por productos, precios o cómo registrar una venta."
    else:
        return f"{t} {icon} ¡Hola! ¿En qué te ayudo?"


@agent_chat_bp.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    d = request.get_json(silent=True) or {}
    msg = str(d.get('mensaje', '')).strip()
    name_from_req = str(d.get('nombre', '')).strip()
    request_id = ensure_request_id(request)

    usuario = session.get('usuario')
    # El cliente puede declarar su rol esperado en el body para casos donde
    # la cookie de sesión se reutiliza entre usuarios (robots E2E, etc.).
    # Si hay mismatch con la sesión, prevalece el de la sesión pero se loguea
    # para auditoría. Esto previene el bug de saludo cruzado entre roles.
    rol_esperado = str(d.get('rol', '')).strip().lower()
    if usuario and isinstance(usuario, dict):
        rol = usuario.get('rol', 'cliente')
        name = usuario.get('nombre') or usuario.get('username') or name_from_req
        # ═══════════════════════════════════════════════════════════════
        # COMANDOS DE DOCUMENTACIÓN (solo desarrollador)
        # ═══════════════════════════════════════════════════════════════
        msg_lower = msg.lower()
        if rol == "desarrollador":
            
            # Documentación completa
            if any(k in msg_lower for k in ["documentacion", "docs", "documentación", "estructura", "endpoints", "rutas", "api docs", "arquitectura"]):
                try:
                    from modules.docs_dev_bp import api_dev_docs as _docs_func
                    import json as _json
                    r = _docs_func()
                    d = r.get_json() if hasattr(r, 'get_json') else _json.loads(r[0].get_data())
                    return jsonify({
                            "ok": True, "tipo": "docs",
                            "respuesta": (
                                "📚 DOCUMENTACIÓN COMPLETA — TPV Ultra Smart v8.14.0\n\n"
                                "══════════ ESTADÍSTICAS ══════════\n"
                                f"🔹 Archivos totales: {d['estadisticas']['total_archivos']}\n"
                                f"🔹 Líneas de código: {d['estadisticas']['lineas_codigo']}\n"
                                f"🔹 Tests: {d['estadisticas']['total_tests']} ({d['estadisticas']['tests_pasan']} pasan)\n"
                                f"🔹 Cobertura backend: {d['estadisticas']['cobertura_backend']}\n"
                                f"🔹 Cobertura E2E: {d['estadisticas']['cobertura_e2e']}\n"
                                f"🔹 Endpoints: {d['endpoints_total']}\n"
                                f"🔹 Blueprints: {len(d['blueprints'])}\n\n"
                                "══════════ MÓDULOS ══════════\n"
                                + "\n".join(f"  📁 {m}: {len(files)} archivos" for m, files in d['modulos'].items()) + "\n\n"
                                "══════════ SEGURIDAD ══════════\n"
                                + "\n".join(f"  🔒 {k}: {v}" for k, v in d['seguridad'].items()) + "\n\n"
                                "══════════ ARREGLOS RECIENTES ══════════\n"
                                + "\n".join(f"  ✅ {a}" for a in d['arreglos_recientes']) + "\n\n"
                                f"📄 Documentos disponibles: {', '.join(d['contenido_documentos'].keys())}\n\n"
                                "Escribe: 'tests' para resultados de pruebas\n"
                                "Escribe: 'documento README' para ver un documento específico"
                            ),
                            "data": d
                        })
                except Exception as _e:
                    print('DEBUG DOCS ERROR:', str(_e))
            
            # Tests
            if any(k in msg_lower for k in ["test", "tests", "cobertura", "coverage", "pytest", "pruebas"]):
                try:
                    from modules.tests_info_bp import api_test_summary as _test_func
                    import json as _json
                    r = _test_func()
                    d = r.get_json() if hasattr(r, 'get_json') else _json.loads(r[0].get_data())
                    return jsonify({
                            "ok": True, "tipo": "tests",
                            "respuesta": (
                                "🧪 RESULTADOS DE TESTS\n\n"
                                f"🔹 Total: {d['total_tests']}\n"
                                f"🔹 Pasan: {d['pasan']} ✅\n"
                                f"🔹 Fallan: {d['fallan']} ❌\n"
                                f"🔹 Cobertura backend: {d['cobertura_backend']}\n"
                                f"🔹 Cobertura E2E: {d['cobertura_e2e']}\n"
                                f"🔹 Archivos de test: {d['archivos_test']}\n\n"
                                "Escribe 'documentación' para ver la estructura completa del proyecto."
                            ),
                            "data": d
                        })
                except Exception as _e:
                    print('DEBUG DOCS ERROR:', str(_e))


        # ─── LECTURA DE DOCUMENTOS MARKDOWN (paginado) ───
        # Estado de lectura por sesión
        if "doc_reader" not in session:
            session["doc_reader"] = {"file": "", "lines": [], "page": 0}
        
        reader = session["doc_reader"]
        
        # Comando: leer documento X
        doc_map = {
            "readme": "README.md", "changelog": "CHANGELOG.md",
            "api": "docs/API_REFERENCE.md", "arquitectura": "docs/ARCHITECTURE.md",
            "backend": "docs/BACKEND_MAP.md", "schema": "docs/DATABASE_SCHEMA.md",
            "tesis": "docs/DOCUMENTACION_TESIS.md", "contributing": "docs/CONTRIBUTING.md",
            "checklist": "docs/CHECKLIST_RELEASE.md", "license": "LICENSE",
            "requirements": "requirements.txt"
        }
        
        for keyword, filename in doc_map.items():
            if rol == "desarrollador" and keyword in msg_lower and ("leer" in msg_lower or "documento" in msg_lower or "abrir" in msg_lower or "mostrar" in msg_lower or keyword == msg_lower.strip()):
                ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
                filepath = os.path.join(ROOT, filename)
                if os.path.exists(filepath):
                    with open(filepath) as f:
                        lines = f.readlines()
                    reader["file"] = filename
                    reader["lines"] = lines
                    reader["page"] = 0
                    session["doc_reader"] = reader
                    # Mostrar primera página
                    page_size = 20
                    page_lines = lines[:page_size]
                    total_pages = (len(lines) + page_size - 1) // page_size
                    texto = "".join(page_lines)
                    return jsonify({
                        "ok": True, "tipo": "documento",
                        "respuesta": (
                            f"📄 {filename} (página 1/{total_pages} — {len(lines)} líneas)\n\n"
                            f"{texto}\n\n"
                            "Escribe 'siguiente' para continuar leyendo."
                        )
                    })
                else:
                    return jsonify({"ok": True, "tipo": "error", "respuesta": f"Documento no encontrado: {filename}"})
        
        # Comando: siguiente página
        if rol == "desarrollador" and msg_lower.strip() in ["siguiente", "next", "continuar"] and reader["lines"]:
            page_size = 20
            reader["page"] += 1
            start = reader["page"] * page_size
            if start >= len(reader["lines"]):
                reader["page"] = 0
                start = 0
            page_lines = reader["lines"][start:start+page_size]
            total_pages = (len(reader["lines"]) + page_size - 1) // page_size
            session["doc_reader"] = reader
            texto = "".join(page_lines)
            return jsonify({
                "ok": True, "tipo": "documento",
                "respuesta": (
                    f"📄 {reader['file']} (página {reader['page']+1}/{total_pages})\n\n"
                    f"{texto}\n\n"
                    "Escribe 'siguiente' para continuar, 'cerrar documento' para salir."
                )
            })
        
        # Comando: cerrar documento
        if rol == "desarrollador" and msg_lower.strip() in ["cerrar documento", "cerrar", "salir documento"]:
            session.pop("doc_reader", None)
            return jsonify({"ok": True, "tipo": "info", "respuesta": "📄 Documento cerrado."})

        # ─── FIN COMANDOS DE DOCUMENTACIÓN ───


        usuario_id = usuario.get('usuario_id', '')
        anon_client_id = session.get('anon_client_id', '')
        autenticado = True
        # Auditoría de mismatch (no bloqueante, solo logging)
        if rol_esperado and rol_esperado != rol:
            import logging
            logging.getLogger(__name__).warning(
                "Rol mismatch en /api/agent/chat: sesion=%s pero request pide=%s "
                "(usuario_id=%s, request_id=%s)",
                rol, rol_esperado, usuario_id, request_id
            )
    else:
        rol = 'cliente'
        anon_client_id = ensure_anon_client_id(request, session)
        name = name_from_req or 'Cliente anónimo'
        usuario_id = anon_client_id
        autenticado = False

    saludos = ['hola', 'buenas', 'hi', 'hey', 'buenos dias', 'buenas tardes', 'buenas noches']
    if not msg or msg.lower().strip() in saludos:
        return jsonify({
            "ok": True,
            "respuesta": _saludo_inteligente(rol, name),
            "rol": rol,
            "intencion": "GREETING",
            "ui_action": None,
            "request_id": request_id,
            "anon_client_id": anon_client_id,
            "usuario_id": usuario_id,
            "autenticado": autenticado,
        })

    try:
        from ia.catalog import P, O
        if hasattr(P, 'load'):
            P.load()
        if hasattr(O, 'load'):
            O.load()
    except Exception:
        pass

    if _agent_loaded and _agent:
        try:
            result = _agent.process(text=msg, role=rol, name=name)
            tools = [f"{t.get('icon', '')} {t.get('name', '')}" for t in result.get('tools', [])]
            return jsonify({
                "ok": True,
                "respuesta": result.get('response', ''),
                "rol": rol,
                "intencion": result.get('intent', ''),
                "confianza": result.get('confidence', 0.85),
                "herramientas": tools,
                "ui_action": result.get('ui_action'),
                "request_id": request_id,
                "anon_client_id": anon_client_id,
                "usuario_id": usuario_id,
                "autenticado": autenticado,
            })
        except Exception as e:
            print(f"Agent error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "ok": True,
                "respuesta": _saludo_inteligente(rol, name),
                "rol": rol,
                "ui_action": None,
                "request_id": request_id,
                "anon_client_id": anon_client_id,
                "usuario_id": usuario_id,
                "autenticado": autenticado,
            })

    return jsonify({
        "ok": True,
        "respuesta": _saludo_inteligente(rol, name) + " (Motor IA no disponible, modo catálogo)",
        "rol": rol,
        "ui_action": None,
        "request_id": request_id,
        "anon_client_id": anon_client_id,
        "usuario_id": usuario_id,
        "autenticado": autenticado,
    })


@agent_chat_bp.route('/api/agent/status')
def agent_status():
    status = {"ok": True, "agent": "fallback", "version": "8.0", "request_id": ensure_request_id(request)}
    if _agent_loaded and _agent:
        try:
            status["agent"] = "active"
            status["details"] = _agent.get_status()
        except Exception:
            status["agent"] = "active"
    return jsonify(status)


@agent_chat_bp.route('/api/agent/identity')
def agent_identity():
    """El frontend llama esto al cargar la página para saber quién es el usuario."""
    return jsonify(identity_payload(request, session))


def is_agent_loaded():
    return _agent_loaded
