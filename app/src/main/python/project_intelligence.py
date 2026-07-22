"""Static project introspection for developer IA and thesis defense.

Uses AST instead of importing modules, so it can describe the repository without
executing side effects or requiring network access.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = SOURCE_ROOT.parents[3]
_EXCLUDED_PARTS = {"tests", "__pycache__", "legacy"}


def _python_files():
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        relative = path.relative_to(SOURCE_ROOT)
        if any(part in _EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.name.startswith("patch_") or "backup" in path.name.lower():
            continue
        yield path, relative.as_posix()


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    arguments = [argument.arg for argument in node.args.args]
    if node.args.vararg:
        arguments.append("*" + node.args.vararg.arg)
    if node.args.kwarg:
        arguments.append("**" + node.args.kwarg.arg)
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}{node.name}({', '.join(arguments)})"


def _route_from_decorator(decorator) -> dict | None:
    if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
        return None
    method = decorator.func.attr.lower()
    if method not in {"route", "get", "post", "put", "delete", "patch"}:
        return None
    if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
        return None
    route = decorator.args[0].value
    methods = [method.upper()] if method != "route" else ["GET"]
    for keyword in decorator.keywords:
        if keyword.arg == "methods" and isinstance(keyword.value, (ast.List, ast.Tuple)):
            methods = [item.value for item in keyword.value.elts if isinstance(item, ast.Constant)]
    return {"path": route, "methods": methods}


def inspect_module(path: Path, relative: str | None = None) -> dict:
    relative = relative or path.relative_to(SOURCE_ROOT).as_posix()
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(text, filename=relative)
    except SyntaxError as exc:
        return {"module": relative, "lines": len(text.splitlines()), "error": str(exc), "functions": [], "classes": [], "routes": []}
    functions, classes, routes = [], [], []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = (ast.get_docstring(node) or "").splitlines()
            functions.append({
                "name": node.name, "signature": _signature(node), "line": node.lineno,
                "description": doc[0] if doc else "",
            })
            for decorator in node.decorator_list:
                route = _route_from_decorator(decorator)
                if route:
                    route.update({"function": node.name, "line": node.lineno})
                    routes.append(route)
        elif isinstance(node, ast.ClassDef):
            methods = [
                {"name": child.name, "signature": _signature(child), "line": child.lineno}
                for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            doc = (ast.get_docstring(node) or "").splitlines()
            classes.append({"name": node.name, "line": node.lineno, "description": doc[0] if doc else "", "methods": methods})
    return {
        "module": relative, "lines": len(text.splitlines()),
        "description": ((ast.get_docstring(tree) or "").splitlines() or [""])[0],
        "functions": functions, "classes": classes, "routes": routes,
    }


def project_inventory() -> dict:
    modules = [inspect_module(path, relative) for path, relative in _python_files()]
    return {
        "source_root": "app/src/main/python",
        "modules_total": len(modules),
        "lines_total": sum(module["lines"] for module in modules),
        "functions_total": sum(len(module["functions"]) for module in modules),
        "classes_total": sum(len(module["classes"]) for module in modules),
        "routes_declared": sum(len(module["routes"]) for module in modules),
        "modules": modules,
    }


def find_modules(query: str, limit: int = 10) -> list[dict]:
    stopwords = {"modulo", "módulo", "modulos", "módulos", "funcion", "función", "funciones", "explica", "explicar", "del", "las", "los", "una", "con"}
    terms = [
        term for term in str(query).lower().replace(".py", "").split()
        if len(term) > 1 and term not in stopwords
    ]
    modules = project_inventory()["modules"]
    if not terms:
        return modules[:limit]
    scored = []
    for module in modules:
        haystack = " ".join([
            module["module"], module.get("description", ""),
            " ".join(item["name"] for item in module["functions"]),
            " ".join(item["name"] for item in module["classes"]),
        ]).lower()
        score = sum(term in haystack for term in terms)
        if score:
            scored.append((score, module["module"], module))
    return [item[2] for item in sorted(scored, key=lambda row: (-row[0], row[1]))[:limit]]


def folder_structure() -> dict:
    result = {}
    for relative in ("app/src/main/python", "app/src/main/java", "app/src/main/assets/frontend", "docs", "tests", "tools", "scripts", "diagramas", ".github"):
        directory = REPOSITORY_ROOT / relative
        if not directory.is_dir():
            continue
        entries = sorted(path.name for path in directory.iterdir() if not path.name.startswith("."))
        result[relative] = entries[:80]
    return result


def _text_files(root: Path, suffixes: set[str]):
    if not root.is_dir():
        return []
    return [
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in suffixes
        and "build" not in path.parts and "node_modules" not in path.parts
    ]


def technology_inventory() -> dict:
    """Inspect frontend, Android, configuration and documentation assets."""
    roots = {
        "frontend": REPOSITORY_ROOT / "app/src/main/assets/frontend",
        "android": REPOSITORY_ROOT / "app/src/main/java",
        "android_resources": REPOSITORY_ROOT / "app/src/main/res",
        "documentation": REPOSITORY_ROOT / "docs",
        "automation": REPOSITORY_ROOT / ".github",
    }
    suffixes = {".js", ".css", ".html", ".java", ".kt", ".xml", ".gradle", ".md", ".yaml", ".yml", ".json", ".sh", ".toml"}
    files = []
    for area, root in roots.items():
        for path in _text_files(root, suffixes):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            files.append({
                "area": area,
                "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
                "type": path.suffix.lower().lstrip("."),
                "lines": len(text.splitlines()),
            })
    special_files = [
        REPOSITORY_ROOT / "app/src/main/AndroidManifest.xml",
        REPOSITORY_ROOT / "app/build.gradle",
        REPOSITORY_ROOT / "build.gradle",
        REPOSITORY_ROOT / "settings.gradle",
        REPOSITORY_ROOT / "pyproject.toml",
    ]
    known_paths = {item["path"] for item in files}
    for path in special_files:
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        if not path.is_file() or relative in known_paths:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        files.append({
            "area": "configuration", "path": relative,
            "type": path.suffix.lower().lstrip("."), "lines": len(text.splitlines()),
        })
    by_type = {}
    for item in files:
        stats = by_type.setdefault(item["type"], {"files": 0, "lines": 0})
        stats["files"] += 1
        stats["lines"] += item["lines"]

    css_files = [REPOSITORY_ROOT / item["path"] for item in files if item["type"] == "css"]
    js_files = [REPOSITORY_ROOT / item["path"] for item in files if item["type"] == "js"]
    html_files = [REPOSITORY_ROOT / item["path"] for item in files if item["type"] == "html"]
    java_files = [REPOSITORY_ROOT / item["path"] for item in files if item["type"] in {"java", "kt"}]
    css_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in css_files)
    js_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in js_files)
    html_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in html_files)
    java_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in java_files)
    return {
        "files_total": len(files),
        "lines_total": sum(item["lines"] for item in files),
        "by_type": by_type,
        "files": files,
        "frontend_analysis": {
            "css_custom_properties": len(set(re.findall(r"--[a-zA-Z0-9_-]+\s*:", css_text))),
            "css_media_queries": len(re.findall(r"@media\b", css_text)),
            "javascript_functions": len(re.findall(r"(?:function\s+[\w$]+|(?:const|let|var)\s+[\w$]+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)", js_text)),
            "html_ids": len(set(re.findall(r"\bid=[\"']([^\"']+)", html_text))),
        },
        "android_analysis": {
            "classes": sorted(set(re.findall(r"\bclass\s+(\w+)", java_text))),
            "methods_approx": len(re.findall(r"\b(?:public|private|protected)\s+[\w<>\[\]]+\s+\w+\s*\(", java_text)),
        },
    }


def architecture_layers() -> list[dict]:
    return [
        {"layer": "Android nativo", "paths": ["app/src/main/java", "AndroidManifest.xml"], "responsibility": "ciclo de vida, WebView, biometría, permisos y Chaquopy"},
        {"layer": "Presentación Web", "paths": ["app/src/main/assets/frontend/templates", "static/css", "static/js"], "responsibility": "HTML, CSS, interacción, accesibilidad y estado visual"},
        {"layer": "API local", "paths": ["app/src/main/python/app.py", "modules/*_bp.py"], "responsibility": "Flask, rutas, sesiones, contratos JSON y blueprints"},
        {"layer": "Dominio", "paths": ["database.py", "db/", "models/", "license/"], "responsibility": "ventas, inventario, usuarios, licencias y reglas"},
        {"layer": "IA", "paths": ["ia/", "ia_assistant.py"], "responsibility": "intents, roles, ReAct, memoria, tools, guardrails y documentación"},
        {"layer": "Telecom", "paths": ["modules/telecom_diag.py", "modules/telecom_bp.py"], "responsibility": "DNS, TCP, TLS, RTT HTTP, P95, jitter, fallos y goodput"},
        {"layer": "Persistencia Edge", "paths": ["SQLite", "TPV_FILES_DIR"], "responsibility": "transacciones locales, WAL, auditoría y documentación offline"},
        {"layer": "Sincronización", "paths": ["supabase_sync.py", "sync/"], "responsibility": "réplica remota opcional sin bloquear la venta"},
        {"layer": "Calidad y entrega", "paths": ["tests/", ".github/", "docs/", "diagramas/"], "responsibility": "pruebas, cobertura, CI, APK y evidencia académica"},
    ]


def osi_model() -> list[dict]:
    return [
        {"layer": 7, "name": "Aplicación", "project": "HTTP/REST Flask, Supabase, IA, JSON API", "measurements": "RTT HTTP, P95, solicitudes fallidas, goodput", "limitation": "incluye servidor y procesamiento"},
        {"layer": 6, "name": "Presentación", "project": "TLS, JSON, UTF-8, serialización", "measurements": "versión TLS, cipher, certificado", "limitation": "TLS suele ubicarse entre aplicación y transporte en TCP/IP"},
        {"layer": 5, "name": "Sesión", "project": "cookie Flask, token de sesión, SSE y onboarding", "measurements": "estado de autenticación y continuidad", "limitation": "capa conceptual en la pila TCP/IP moderna"},
        {"layer": 4, "name": "Transporte", "project": "TCP 443 y loopback local", "measurements": "tiempo de conexión TCP", "limitation": "no captura retransmisiones sin instrumentación adicional"},
        {"layer": 3, "name": "Red", "project": "IPv4/IPv6, DNS resuelto y direccionamiento", "measurements": "IPs local/remota", "limitation": "no ejecuta ICMP raw ni captura rutas"},
        {"layer": 2, "name": "Enlace", "project": "Wi-Fi o red celular administrada por Android", "measurements": "tipo de enlace futuro", "limitation": "sin acceso Python directo a tramas, RSRP o RSRQ"},
        {"layer": 1, "name": "Física", "project": "radio, antena, canal y dispositivo", "measurements": "no medidas actualmente", "limitation": "requiere TelephonyManager/WifiManager y permisos con consentimiento"},
    ]


def chaquopy_profile() -> dict:
    """Describe the Android/Python bridge from the real Gradle configuration."""
    gradle_path = REPOSITORY_ROOT / "app/build.gradle"
    gradle = gradle_path.read_text(encoding="utf-8", errors="ignore") if gradle_path.is_file() else ""
    python_version = (re.search(r'python\s*\{[\s\S]*?version\s+[\"\']([^\"\']+)', gradle) or [None, "unknown"])[1]
    abi_match = re.search(r'abiFilters\s+([^\n]+)', gradle)
    abis = re.findall(r'[\"\']([^\"\']+)[\"\']', abi_match.group(1)) if abi_match else []
    pip_packages = re.findall(r'install\s+[\"\']([^\"\']+)[\"\']', gradle)
    return {
        "plugin": "com.chaquo.python",
        "python_version": python_version,
        "abis": abis,
        "pip_packages": pip_packages,
        "android_entry": "MainApplication/MainActivity",
        "python_entry": "app/src/main/python/start_server.py",
        "flask_binding": "127.0.0.1:5050 dentro de la APK",
        "data_bridge": {
            "TPV_FILES_DIR": "directorio Android escribible para SQLite y secretos",
            "TPV_FRONTEND_DIR": "assets frontend expuestos al backend local",
            "TPV_DB_PATH": "ruta SQLite compartida por motores IA",
        },
        "startup_flow": [
            "Android crea el runtime Chaquopy", "Java publica directorios mediante System properties",
            "start_server.py configura variables", "Flask y SQLite se inicializan",
            "WebView consume HTTP loopback",
        ],
        "advantages": [
            "reutilización del backend Python", "operación offline", "ecosistema Flask/SQLite",
            "misma lógica en Termux, CI y Android",
        ],
        "limitations": [
            "compatibilidad Python fijada por Chaquopy", "wheels deben soportar ABI Android",
            "no escribir dentro del source empaquetado", "tamaño APK aumenta con dependencias/modelos",
        ],
    }


def diagram_inventory() -> dict:
    root = REPOSITORY_ROOT / "diagramas"
    diagrams = []
    if root.is_dir():
        stems = {}
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".puml", ".svg", ".png"}:
                continue
            relative = path.relative_to(REPOSITORY_ROOT).as_posix()
            key = path.with_suffix("").relative_to(root).as_posix()
            item = stems.setdefault(key, {"name": key, "sources": [], "title": ""})
            item["sources"].append(relative)
            if path.suffix.lower() == ".puml":
                text = path.read_text(encoding="utf-8", errors="ignore")
                title = re.search(r"^title\s+(.+)$", text, re.MULTILINE)
                item["title"] = title.group(1).strip() if title else path.stem.replace("_", " ")
        diagrams = list(stems.values())
    return {
        "total": len(diagrams),
        "formats": {
            extension: sum(any(source.endswith(extension) for source in item["sources"]) for item in diagrams)
            for extension in (".puml", ".svg", ".png")
        },
        "groups": sorted({item["name"].split("/")[0] for item in diagrams}),
        "diagrams": diagrams,
    }


def state_of_the_art() -> dict:
    """Structured comparison used by IA; full rationale lives in docs."""
    return {
        "scope": "TPV móvil offline-first, IA edge y observabilidad Telecom",
        "approaches": [
            {"approach": "POS cloud puro", "strength": "gestión central", "gap": "dependencia WAN", "project_response": "SQLite local + sync opcional"},
            {"approach": "POS Android local", "strength": "continuidad", "gap": "poca inteligencia/telemetría", "project_response": "IA por roles + diagnóstico por capas"},
            {"approach": "chatbot cloud", "strength": "lenguaje flexible", "gap": "costo, privacidad, offline", "project_response": "motor intents/ReAct/memoria local; LLM opcional"},
            {"approach": "monitor de red aislado", "strength": "KPIs técnicos", "gap": "no correlaciona operación", "project_response": "Telecom integrado al flujo TPV"},
            {"approach": "PWA", "strength": "portabilidad", "gap": "acceso nativo limitado", "project_response": "WebView + Chaquopy + biometría Android"},
        ],
        "differentiators": [
            "venta local independiente de WAN", "IA explicable por rol", "documentación consultable offline",
            "mediciones Telecom con método/unidad/limitación", "mismo backend en Android, Termux y CI",
        ],
        "research_gap": "Integrar continuidad transaccional, IA edge y diagnóstico Telecom verificable en una APK educativa reproducible",
        "evidence": [
            "tests y cobertura", "CI y APK", "experimentos Wi-Fi/celular/offline",
            "diagramas de despliegue, datos, IA, CI y Telecom",
        ],
        "caveat": "La comparación es técnica y conceptual; una revisión bibliográfica formal debe citar fuentes académicas externas según la norma de la universidad",
    }


def thesis_defense_summary() -> dict:
    inventory = project_inventory()
    technology = technology_inventory()
    return {
        "project": "TPV Ultra Smart",
        "version": "6.13.1",
        "degree": "Ingeniería en Telecomunicaciones",
        "problem": "Continuidad de ventas sobre conectividad WAN variable",
        "hypothesis": "El plano transaccional SQLite mantiene la operación y sincroniza cuando vuelve la WAN",
        "architecture": ["Android/WebView", "HTML/CSS/JavaScript", "Flask local", "SQLite WAL", "IA por roles", "Supabase opcional"],
        "architecture_layers": architecture_layers(),
        "osi_model": osi_model(),
        "chaquopy": chaquopy_profile(),
        "diagrams": diagram_inventory(),
        "state_of_the_art": state_of_the_art(),
        "technology_summary": {key: technology[key] for key in ("files_total", "lines_total", "by_type", "frontend_analysis", "android_analysis")},
        "telecom": ["DNS", "TCP", "TLS", "RTT HTTP", "P95", "jitter observado", "solicitudes fallidas", "goodput", "SQLite ops/s"],
        "ia": ["intents", "handlers por rol", "ReAct", "memoria", "skills", "cache", "guardrails", "documentación offline"],
        "security": ["onboarding local", "identidad Desarrollador única", "contraseña exclusiva", "sesión con token", "auditoría", "SQLi/XSS"],
        "quality": {"coverage_gate": ">=50%", "ci": "tests antes del APK", "resource_warnings": "tratados como error"},
        "inventory_summary": {key: inventory[key] for key in ("modules_total", "lines_total", "functions_total", "classes_total", "routes_declared")},
        "limitations": [
            "RTT HTTP no equivale a ICMP", "goodput no equivale a capacidad física",
            "LLM local es opcional", "diagnóstico radio avanzado requiere APIs Android nativas",
        ],
        "future_work": [
            "release firmada", "mediciones reales por escenario", "dashboard temporal Telecom",
            "exportación CSV anonimizada", "TelephonyManager para RSRP/RSRQ/SINR con consentimiento",
            "cobertura >=60% de módulos activos",
        ],
        "documents": [
            "README.md", "docs/ARCHITECTURE.md", "docs/TELECOM_ENGINEERING.md",
            "docs/telecom_diagnostico.md", "docs/DEVELOPER_GUIDE.md",
            "docs/API_REFERENCE.md", "docs/DATABASE_SCHEMA.md", "docs/ROADMAP_10_10.md",
        ],
    }


def format_module_report(modules: list[dict]) -> str:
    lines = []
    for module in modules:
        lines.append(f"MÓDULO {module['module']} ({module['lines']} líneas)")
        if module.get("description"):
            lines.append("  " + module["description"])
        for function in module["functions"]:
            lines.append(f"  función L{function['line']}: {function['signature']} — {function['description']}")
        for class_info in module["classes"]:
            lines.append(f"  clase L{class_info['line']}: {class_info['name']} — {class_info['description']}")
            for method in class_info["methods"]:
                lines.append(f"    método L{method['line']}: {method['signature']}")
        for route in module["routes"]:
            lines.append(f"  API {'/'.join(route['methods'])} {route['path']} -> {route['function']}")
        lines.append("")
    return "\n".join(lines).strip()


def json_inventory() -> str:
    return json.dumps(project_inventory(), ensure_ascii=False, indent=2)
