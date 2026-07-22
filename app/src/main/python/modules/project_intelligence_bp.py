"""Developer-only API exposing static project intelligence for thesis defense."""
from __future__ import annotations

from functools import wraps

from flask import Blueprint, jsonify, request, session

from project_intelligence import (
    architecture_layers, find_modules, folder_structure, osi_model,
    project_inventory, technology_inventory, thesis_defense_summary,
)

project_intelligence_bp = Blueprint("project_intelligence", __name__)


def _developer_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        user = session.get("usuario") or {}
        if user.get("rol") != "desarrollador":
            return jsonify({"ok": False, "error": "Solo desarrollador"}), 403
        return function(*args, **kwargs)
    return wrapper


@project_intelligence_bp.get("/api/dev/project/summary")
@_developer_required
def project_summary():
    inventory = project_inventory()
    return jsonify({
        "ok": True,
        "summary": {key: inventory[key] for key in (
            "source_root", "modules_total", "lines_total", "functions_total",
            "classes_total", "routes_declared",
        )},
    })


@project_intelligence_bp.get("/api/dev/project/inventory")
@_developer_required
def project_full_inventory():
    """Return the complete AST inventory without conversational truncation."""
    return jsonify({"ok": True, "inventory": project_inventory()})


@project_intelligence_bp.get("/api/dev/project/modules")
@_developer_required
def project_modules():
    query = request.args.get("q", "")
    limit = min(max(request.args.get("limit", 10, type=int), 1), 50)
    return jsonify({"ok": True, "query": query, "modules": find_modules(query, limit=limit)})


@project_intelligence_bp.get("/api/dev/project/structure")
@_developer_required
def project_structure():
    return jsonify({"ok": True, "structure": folder_structure()})


@project_intelligence_bp.get("/api/dev/project/layers")
@_developer_required
def project_layers():
    return jsonify({"ok": True, "architecture": architecture_layers(), "osi": osi_model()})


@project_intelligence_bp.get("/api/dev/project/technology")
@_developer_required
def project_technology():
    return jsonify({"ok": True, "technology": technology_inventory()})


@project_intelligence_bp.get("/api/dev/project/thesis")
@_developer_required
def project_thesis():
    return jsonify({"ok": True, "thesis": thesis_defense_summary()})
