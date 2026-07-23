"""Project intelligence supports exhaustive developer and thesis discussion."""
from __future__ import annotations

import json

from ia.handlers_staff import handle_dev
from project_intelligence import (
    architecture_layers, chaquopy_profile, diagram_inventory, find_modules,
    folder_structure, format_module_report, inspect_module, osi_model,
    project_inventory, state_of_the_art, technology_inventory,
    thesis_defense_summary,
)


def test_inventory_discovers_real_functions_classes_and_routes():
    inventory = project_inventory()
    assert inventory["modules_total"] > 100
    assert inventory["functions_total"] > 200
    assert inventory["classes_total"] > 20
    assert inventory["routes_declared"] > 100
    app_module = next(module for module in inventory["modules"] if module["module"] == "app.py")
    assert any(function["name"] == "main" for function in app_module["functions"])
    assert any(route["path"] == "/api/setup/status" for route in app_module["routes"])


def test_module_search_and_report_include_signatures_and_lines():
    modules = find_modules("telecom diagnostico", limit=5)
    assert any(module["module"].endswith("telecom_diag.py") for module in modules)
    report = format_module_report(modules)
    assert "función L" in report
    assert "medir_latencia_supabase" in report
    assert "MÓDULO" in report


def test_multilanguage_inventory_and_osi_cover_every_layer():
    technology = technology_inventory()
    for file_type in ("js", "css", "html", "java", "xml", "md", "yaml"):
        assert technology["by_type"][file_type]["files"] > 0
    assert technology["frontend_analysis"]["javascript_functions"] > 20
    assert technology["frontend_analysis"]["html_ids"] > 20
    assert technology["android_analysis"]["classes"]
    layers = architecture_layers()
    assert len(layers) >= 9
    osi = osi_model()
    assert [item["layer"] for item in osi] == [7, 6, 5, 4, 3, 2, 1]
    assert "no medidas" in osi[-1]["measurements"]


def test_chaquopy_diagrams_and_state_of_art_are_traceable():
    chaquopy = chaquopy_profile()
    assert chaquopy["plugin"] == "com.chaquo.python"
    assert chaquopy["python_version"] == "3.10"
    assert "arm64-v8a" in chaquopy["abis"]
    assert any(package.startswith("flask") for package in chaquopy["pip_packages"])
    diagrams = diagram_inventory()
    assert diagrams["total"] >= 10
    assert diagrams["formats"][".puml"] >= 1
    assert "trabajo4" in diagrams["groups"]
    art = state_of_the_art()
    assert len(art["approaches"]) >= 5
    assert art["research_gap"]
    assert "bibliográfica" in art["caveat"]


def test_structure_and_thesis_cover_discussion_without_fake_metrics():
    structure = folder_structure()
    assert "app/src/main/python" in structure
    assert "docs" in structure
    thesis = thesis_defense_summary()
    assert thesis["degree"] == "Ingeniería en Telecomunicaciones"
    assert "RTT HTTP" in thesis["telecom"]
    assert thesis["quality"]["coverage_gate"] == ">=50%"
    assert thesis["limitations"]
    assert thesis["future_work"]


def test_project_intelligence_api_is_developer_only():
    from app import app

    app.config.update(TESTING=True, SECRET_KEY="project-intelligence-test")
    anonymous = app.test_client()
    assert anonymous.get("/api/dev/project/summary").status_code == 403
    client = app.test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"usuario_id": "dev", "rol": "desarrollador"}
    summary = client.get("/api/dev/project/summary").get_json()
    assert summary["ok"] and summary["summary"]["modules_total"] > 100
    assert client.get("/api/dev/project/modules?q=telecom&limit=2").status_code == 200
    full = client.get("/api/dev/project/inventory").get_json()
    assert full["inventory"]["functions_total"] > 200
    assert client.get("/api/dev/project/structure").status_code == 200
    layers = client.get("/api/dev/project/layers").get_json()
    assert len(layers["osi"]) == 7
    technology = client.get("/api/dev/project/technology").get_json()
    assert technology["technology"]["by_type"]["css"]["files"] > 0
    assert client.get("/api/dev/project/chaquopy").get_json()["chaquopy"]["python_version"] == "3.10"
    assert client.get("/api/dev/project/diagrams").get_json()["diagrams"]["total"] >= 10
    assert client.get("/api/dev/project/state-of-art").status_code == 200
    assert client.get("/api/dev/project/thesis").status_code == 200


def test_developer_commands_expose_thesis_structure_and_modules():
    thesis = json.loads(handle_dev(None, "defensa completa", "Developer"))
    assert thesis["hypothesis"]
    structure = json.loads(handle_dev(None, "estructura de carpetas", "Developer"))
    assert "docs" in structure
    modules = handle_dev(None, "módulos y funciones telecom", "Developer")
    assert "telecom_diag.py" in modules
    assert "medir_tls_handshake" in modules
    osi = handle_dev(None, "capas OSI", "Developer")
    assert "Capa 7" in osi and "Capa 1" in osi
    css = json.loads(handle_dev(None, "frontend CSS", "Developer"))
    assert css["by_type"]["css"]["files"] > 0
    assert all(item["type"] == "css" for item in css["files"])
    chaquopy = handle_dev(None, "Chaquopy", "Developer")
    assert "Python embebido: 3.10" in chaquopy
    assert "Ventajas" in chaquopy and "Limitaciones" in chaquopy
    diagrams = handle_dev(None, "diagramas", "Developer")
    assert "Catálogo de diagramas" in diagrams
    art = handle_dev(None, "estado del arte", "Developer")
    assert "Brecha:" in art and "Diferenciadores" in art
