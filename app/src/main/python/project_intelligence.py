"""Static project introspection for developer IA and thesis defense.

Uses AST instead of importing modules, so it can describe the repository without
executing side effects or requiring network access.
"""
from __future__ import annotations

import ast
import json
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
    for relative in ("app/src/main/python", "app/src/main/assets/frontend", "docs", "tests", "tools", "scripts", "diagramas"):
        directory = REPOSITORY_ROOT / relative
        if not directory.is_dir():
            continue
        entries = sorted(path.name for path in directory.iterdir() if not path.name.startswith("."))
        result[relative] = entries[:80]
    return result


def thesis_defense_summary() -> dict:
    inventory = project_inventory()
    return {
        "project": "TPV Ultra Smart",
        "version": "6.13.1",
        "degree": "Ingeniería en Telecomunicaciones",
        "problem": "Continuidad de ventas sobre conectividad WAN variable",
        "hypothesis": "El plano transaccional SQLite mantiene la operación y sincroniza cuando vuelve la WAN",
        "architecture": ["Android/WebView", "Flask local", "SQLite WAL", "IA por roles", "Supabase opcional"],
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
