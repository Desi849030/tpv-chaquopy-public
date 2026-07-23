# -*- coding: utf-8 -*-
"""Blueprint: Agente IA chat + status (v8.0 definitivo)."""

try:
    from ia.agent_master import agent_master
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    agent_master = None

from flask import Blueprint, request, jsonify, session, current_app
import os
from datetime import datetime

from anon_identity import ensure_anon_client_id, ensure_request_id, identity_payload
from version import __version__

agent_chat_bp = Blueprint('agent_chat', __name__)

_agent = None
_agent_loaded = False
try:
    # Motor conversacional principal. El código anterior intentaba importar
    # `agent` desde ia.agent_master, pero ese módulo expone `agent_master`, no
    # `agent`; por eso en APK aparecía: "Agente IA no disponible" y el chat
    # caía siempre al modo catálogo. ia.agent sí expone process_question(),
    # get_status() y el pipeline modular completo.
    from ia import agent as _agent
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
            
            # Catálogo documental completo, sin cargar contenidos en la cookie.
            catalog_terms = [
                "documentacion", "documentación", "docs", "todos los documentos",
                "lista de documentos", "listar documentos", "catalogo documental",
                "catálogo documental", "indice documental", "índice documental",
            ]
            if any(term in msg_lower for term in catalog_terms):
                from db_connection import obtener_conexion
                from documentation_loader import canonical_document_catalog

                from documentation_explainer import document_overview
                conn = obtener_conexion()
                try:
                    catalog = canonical_document_catalog(conn)
                    for item in catalog:
                        overview = document_overview(conn, item["nombre"])
                        item["proposito"] = overview["proposito"] if overview else "Documento técnico indexado."
                finally:
                    conn.close()
                response_lines = [
                    f"Centro documental de TPV Ultra Smart v{__version__}",
                    f"He encontrado {len(catalog)} documentos únicos, organizados por tema.",
                    "",
                ]
                current_category = None
                for index, item in enumerate(catalog, 1):
                    item["numero"] = index
                    if item["categoria"] != current_category:
                        current_category = item["categoria"]
                        response_lines.extend(["", current_category.upper()])
                    response_lines.append(
                        f"  {index:02d}. {item['nombre']} ({item['lineas']} líneas)"
                    )
                    response_lines.append(f"      {item['proposito']}")
                response_lines.extend([
                    "", "¿Qué deseas consultar? Escribe: lee el documento <nombre>.",
                    "Si es largo, usa 'siguiente' hasta llegar a la última página.",
                ])
                return jsonify({
                    "ok": True, "tipo": "docs_catalog", "rol": rol,
                    "respuesta": "\n".join(response_lines),
                    "total_documentos": len(catalog), "documentos": catalog,
                })

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
                    import traceback
                    print('DEBUG DOCS ERROR:', str(_e))
                    traceback.print_exc()


        # ─── LECTURA DE DOCUMENTOS MARKDOWN (paginado) ───
        # Estado de lectura por sesión
        if "doc_reader" not in session:
            session["doc_reader"] = {"file": "", "page": 0}
        
        reader = session["doc_reader"]

        # Explicación previa: propósito y estructura antes de mostrar contenido.
        explain_commands = ("explica el documento", "explica documento", "resume el documento", "resumen del documento")
        if rol == "desarrollador" and any(command in msg_lower for command in explain_commands):
            from db_connection import obtener_conexion
            from documentation_explainer import document_overview, format_document_overview

            conn = obtener_conexion()
            try:
                overview = document_overview(conn, msg_lower)
            finally:
                conn.close()
            if overview:
                return jsonify({
                    "ok": True, "tipo": "doc_overview", "rol": rol,
                    "respuesta": format_document_overview(overview),
                    "documento": overview,
                })

        # Generic resolver: any synchronized repository document can be opened,
        # not only the aliases maintained below for common requests.
        read_commands = ("leer", "lee", "abrir", "abre", "mostrar", "muestra", "documento")
        if rol == "desarrollador" and any(command in msg_lower for command in read_commands):
            from db_connection import obtener_conexion
            from documentation_loader import find_document

            conn = obtener_conexion()
            try:
                matched = find_document(conn, msg_lower)
            finally:
                conn.close()
            if matched:
                filename, content, _line_count = matched
                lines = content.splitlines()
                reader = {"file": filename, "page": 0}
                session["doc_reader"] = reader
                page_size = 20
                total_pages = max(1, (len(lines) + page_size - 1) // page_size)
                text = "\n".join(lines[:page_size])
                return jsonify({
                    "ok": True,
                    "tipo": "documento",
                    "respuesta": (
                        f"📄 {filename} (página 1/{total_pages} — {len(lines)} líneas)\n\n"
                        f"{text}\n\nEscribe 'siguiente' para continuar leyendo."
                    ),
                })
        
        # Common aliases kept for concise natural-language commands.
        doc_map = {
                "licencia": "LICENSE", "licence": "LICENSE", "license": "LICENSE",
                "api reference": "docs/API_REFERENCE.md", "api_ref": "docs/API_REFERENCE.md", "endpoints": "docs/API_REFERENCE.md",
                "arquitectura": "docs/ARCHITECTURE.md", "architecture": "docs/ARCHITECTURE.md",
                "mapa": "docs/BACKEND_MAP.md", "mapa backend": "docs/BACKEND_MAP.md", "backend map": "docs/BACKEND_MAP.md",
                "base de datos": "docs/DATABASE_SCHEMA.md", "database": "docs/DATABASE_SCHEMA.md", "schema": "docs/DATABASE_SCHEMA.md",
                "tesis": "docs/DOCUMENTACION_TESIS.md", "documentacion tesis": "docs/DOCUMENTACION_TESIS.md", "doc tesis": "docs/DOCUMENTACION_TESIS.md",
                "contribuir": "docs/CONTRIBUTING.md", "contributing": "docs/CONTRIBUTING.md", "como contribuir": "docs/CONTRIBUTING.md",
                "checklist": "docs/CHECKLIST_RELEASE.md", "release": "docs/CHECKLIST_RELEASE.md", "lanzamiento": "docs/CHECKLIST_RELEASE.md",
                "requisitos": "requirements.txt", "requirements": "requirements.txt", "dependencias": "requirements.txt",
                "desarrollador": "DEVELOPER_GUIDE.md", "developer": "DEVELOPER_GUIDE.md",
                "acceso total": "DEVELOPER_GUIDE.md", "sin limites": "DEVELOPER_GUIDE.md",
                "roadmap": "ROADMAP_10_10.md", "10/10": "ROADMAP_10_10.md",
                "registro cambios": "CHANGELOG.md", "changelog": "CHANGELOG.md", "cambios": "CHANGELOG.md", "historial": "CHANGELOG.md",
            "readme": "README.md", "changelog": "CHANGELOG.md",
            "api": "docs/API_REFERENCE.md", "arquitectura": "docs/ARCHITECTURE.md",
            "backend": "docs/BACKEND_MAP.md", "schema": "docs/DATABASE_SCHEMA.md",
            "tesis": "docs/DOCUMENTACION_TESIS.md", "contributing": "docs/CONTRIBUTING.md",
            "checklist": "docs/CHECKLIST_RELEASE.md", "license": "LICENSE",
            "requirements": "requirements.txt"
        }
        
        for keyword, filename in doc_map.items():
            if rol == "desarrollador" and keyword in msg_lower and ("leer" in msg_lower or "documento" in msg_lower or "abrir" in msg_lower or "mostrar" in msg_lower or keyword == msg_lower.strip()):
                from db_connection import obtener_conexion
                conn = obtener_conexion()
                row = conn.execute("SELECT contenido FROM documentacion WHERE nombre=?", (os.path.basename(filename),)).fetchone()
                conn.close()
                if row:
                    lines = row[0].split('\n')
                    reader = {"file": os.path.basename(filename), "page": 0}
                    session["doc_reader"] = reader
                    # Mostrar primera página
                    page_size = 20
                    page_lines = lines[:page_size]
                    total_pages = (len(lines) + page_size - 1) // page_size
                    texto = "\n".join(page_lines)
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
        
        # Comando: siguiente página. El contenido se recarga desde SQLite para
        # mantener la cookie de sesión pequeña y no perder páginas en WebView.
        if rol == "desarrollador" and msg_lower.strip() in ["siguiente", "next", "continuar"] and reader.get("file"):
            from db_connection import obtener_conexion
            conn = obtener_conexion()
            try:
                row = conn.execute(
                    "SELECT contenido FROM documentacion WHERE nombre=?", (reader["file"],)
                ).fetchone()
            finally:
                conn.close()
            if row:
                lines = row[0].splitlines()
                page_size = 20
                total_pages = max(1, (len(lines) + page_size - 1) // page_size)
                reader["page"] = min(reader.get("page", 0) + 1, total_pages - 1)
                start = reader["page"] * page_size
                page_lines = lines[start:start + page_size]
                session["doc_reader"] = reader
                texto = "\n".join(page_lines)
                final_note = (
                    "Última página. Escribe 'cerrar documento'."
                    if reader["page"] + 1 >= total_pages
                    else "Escribe 'siguiente' para continuar, 'cerrar documento' para salir."
                )
                return jsonify({
                    "ok": True, "tipo": "documento",
                    "respuesta": (
                        f"📄 {reader['file']} (página {reader['page']+1}/{total_pages})\n\n"
                        f"{texto}\n\n{final_note}"
                    )
                })
        
        # Comando: cerrar documento
        if rol == "desarrollador" and msg_lower.strip() in ["cerrar documento", "cerrar", "salir documento"]:
            session.pop("doc_reader", None)
            return jsonify({"ok": True, "tipo": "info", "respuesta": "📄 Documento cerrado."})


        # ─── LEER DOCUMENTOS ───
        if rol == "desarrollador":
            doc_map = {
                "licencia": "LICENSE", "licence": "LICENSE", "license": "LICENSE",
                "api reference": "docs/API_REFERENCE.md", "api_ref": "docs/API_REFERENCE.md", "endpoints": "docs/API_REFERENCE.md",
                "arquitectura": "docs/ARCHITECTURE.md", "architecture": "docs/ARCHITECTURE.md",
                "mapa": "docs/BACKEND_MAP.md", "mapa backend": "docs/BACKEND_MAP.md", "backend map": "docs/BACKEND_MAP.md",
                "base de datos": "docs/DATABASE_SCHEMA.md", "database": "docs/DATABASE_SCHEMA.md", "schema": "docs/DATABASE_SCHEMA.md",
                "tesis": "docs/DOCUMENTACION_TESIS.md", "documentacion tesis": "docs/DOCUMENTACION_TESIS.md", "doc tesis": "docs/DOCUMENTACION_TESIS.md",
                "contribuir": "docs/CONTRIBUTING.md", "contributing": "docs/CONTRIBUTING.md", "como contribuir": "docs/CONTRIBUTING.md",
                "checklist": "docs/CHECKLIST_RELEASE.md", "release": "docs/CHECKLIST_RELEASE.md", "lanzamiento": "docs/CHECKLIST_RELEASE.md",
                "requisitos": "requirements.txt", "requirements": "requirements.txt", "dependencias": "requirements.txt",
                "desarrollador": "DEVELOPER_GUIDE.md", "developer": "DEVELOPER_GUIDE.md",
                "acceso total": "DEVELOPER_GUIDE.md", "sin limites": "DEVELOPER_GUIDE.md",
                "roadmap": "ROADMAP_10_10.md", "10/10": "ROADMAP_10_10.md",
                "registro cambios": "CHANGELOG.md", "changelog": "CHANGELOG.md", "cambios": "CHANGELOG.md", "historial": "CHANGELOG.md",
                "readme": "README.md", "changelog": "CHANGELOG.md",
                "api": "docs/API_REFERENCE.md", "arquitectura": "docs/ARCHITECTURE.md",
                "backend": "docs/BACKEND_MAP.md", "schema": "docs/DATABASE_SCHEMA.md",
                "tesis": "docs/DOCUMENTACION_TESIS.md", "contributing": "docs/CONTRIBUTING.md",
                "checklist": "docs/CHECKLIST_RELEASE.md", "requirements": "requirements.txt"
            }
            for keyword, filename in doc_map.items():
                if keyword in msg_lower and any(k in msg_lower for k in ["leer", "abrir", "mostrar", "ver", "documento", "doc", "lee", "abre", "muestra", "dame", "quiero", "enseñame", "mostrame", "consultar", "revisar", "ver el", "ver la", "lee el", "lee la", "abre el", "abre la", "dame el", "dame la", "mostrar el", "mostrar la", "quiero ver", "quiero leer", "quiero el", "necesito ver", "necesito leer", "puedes mostrar", "puedes darme", "podrias mostrar", "podrias darme"]):
                    try:
                        from db_connection import obtener_conexion
                        conn = obtener_conexion()
                        row = conn.execute(
                            "SELECT contenido FROM documentacion WHERE nombre=?",
                            (os.path.basename(filename),),
                        ).fetchone()
                        conn.close()
                        if row:
                            lines = row[0].split("\n")
                            texto = "\n".join(lines[:10])
                            total = len(lines)
                            return jsonify({"ok": True, "tipo": "documento", "respuesta": f"📄 {filename} (primeras 10/{total} líneas)\n\n{texto}\n\nEscribe 'siguiente' para continuar."})
                    except:
                        pass
        
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
            if hasattr(_agent, 'process_question'):
                result = _agent.process_question(
                    str(usuario_id or request_id), msg,
                    role=rol, user_name=name,
                    user_session={"request_id": request_id, "autenticado": autenticado},
                )
            elif hasattr(_agent, 'agent_master'):
                result = _agent.agent_master.process(msg, user_id=str(usuario_id or request_id), role=rol)
            elif hasattr(_agent, 'process'):
                result = _agent.process(text=msg, role=rol, name=name)
            else:
                raise RuntimeError('Motor IA sin método process compatible')

            respuesta = (result.get('response') or result.get('answer') or
                         result.get('respuesta') or result.get('message') or '')
            tools_raw = result.get('tools') or result.get('tools_used') or []
            tools = []
            for t in tools_raw:
                if isinstance(t, dict):
                    tools.append(f"{t.get('icon', '')} {t.get('name') or t.get('tool') or ''}".strip())
                else:
                    tools.append(str(t))
            return jsonify({
                "ok": True,
                "respuesta": respuesta,
                "rol": rol,
                "intencion": result.get('intent', ''),
                "confianza": result.get('confidence', 0.85),
                "herramientas": tools,
                "ui_action": result.get('ui_action'),
                "modo": result.get('mode', 'classic'),
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

    # === FALLBACK OFFLINE ROBUSTO ===
    # Si el agente no cargo (Chaquopy no encontro el modulo), intentar
    # usar los handlers directamente sin pasar por ia.agent
    try:
        from ia.handlers import handle_cliente, handle_vendedor, handle_cajero
        from ia.handlers_staff import handle_supervisor, handle_admin, handle_dev
        _dispatch = {
            'cliente': handle_cliente,
            'vendedor': handle_vendedor,
            'cajero': handle_cajero,
            'supervisor': handle_supervisor,
            'administrador': handle_admin,
            'desarrollador': handle_dev,
        }
        handler = _dispatch.get(rol, handle_cliente)
        answer = handler(None, msg, name)
        return jsonify({
            "ok": True,
            "respuesta": answer,
            "rol": rol,
            "intencion": "offline_fallback",
            "modo": "offline",
            "ui_action": None,
            "request_id": request_id,
            "anon_client_id": anon_client_id,
            "usuario_id": usuario_id,
            "autenticado": autenticado,
        })
    except Exception as fb_err:
        import traceback
        traceback.print_exc()
        return jsonify({
            "ok": True,
            "respuesta": _saludo_inteligente(rol, name) + "\n\n(Modo offline directo. Puedo ayudarte con productos, ventas y stock.)",
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
            if hasattr(_agent, 'get_status'):
                status["details"] = _agent.get_status()
            elif hasattr(_agent, 'agent_master'):
                status["details"] = {"status": "active", "engine": "agent_master"}
        except Exception:
            status["agent"] = "active"
    return jsonify(status)


@agent_chat_bp.route('/api/agent/identity')
def agent_identity():
    """El frontend llama esto al cargar la página para saber quién es el usuario."""
    return jsonify(identity_payload(request, session))


def is_agent_loaded():
    return _agent_loaded
