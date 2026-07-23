"""Deterministic, plain-language explanations of indexed project documents."""
from __future__ import annotations

import re
from pathlib import Path

from documentation_loader import canonical_document_catalog, find_document


_DESCRIPTIONS = {
    "README.md": "Vista general verificable: propósito, instalación, arquitectura, roles, calidad y entrega.",
    "docs/PROJECT_MASTER_GUIDE.md": "Guía maestra y fuente principal para comprender el proyecto completo.",
    "docs/ARCHITECTURE.md": "Capas, componentes, flujos, decisiones y deuda técnica de la solución.",
    "docs/SYSTEM_LAYERS_AND_OSI.md": "Relación entre arquitectura, tecnologías y las siete capas OSI.",
    "docs/TELECOM_ENGINEERING.md": "Problema, hipótesis, variables y método experimental de Telecomunicaciones.",
    "docs/telecom_diagnostico.md": "Definición rigurosa de KPIs Telecom, unidades, API y limitaciones.",
    "docs/CHAQUOPY_INTEGRATION.md": "Puente Android–Python, arranque, ABI, dependencias, ventajas y límites.",
    "docs/STATE_OF_THE_ART.md": "Comparación técnica, brecha de investigación y diferenciadores.",
    "docs/THESIS_DEFENSE_GUIDE.md": "Guion para explicar, defender y reconocer límites ante el jurado.",
    "docs/DEVELOPER_GUIDE.md": "Acceso, seguridad, comandos, mantenimiento y política del Desarrollador.",
    "docs/API_REFERENCE.md": "Inventario autogenerado de endpoints declarados en el código.",
    "docs/openapi.yaml": "Contrato OpenAPI de endpoints principales y APIs de desarrollo.",
    "docs/DATABASE_SCHEMA.md": "Tablas, campos y relaciones del almacenamiento SQLite.",
    "docs/ROADMAP_10_10.md": "Estado, prioridades pendientes y definición de release terminada.",
    "docs/UI_UX_AND_SECURITY_FINAL.md": "Criterios responsive, accesibilidad, dinamismo y hardening final.",
    "docs/DIAGRAMS_CATALOG.md": "Índice y uso académico de diagramas PlantUML, SVG y PNG.",
    "SECURITY.md": "Política de secretos, autenticación, reportes y controles del proyecto.",
    "CHANGELOG.md": "Historial cronológico de cambios implementados.",
}


def _clean_markdown(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_`>#|]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _first_explanatory_paragraph(content: str) -> str:
    paragraphs = re.split(r"\n\s*\n", content)
    for paragraph in paragraphs:
        cleaned = _clean_markdown(paragraph)
        if len(cleaned) >= 45 and not cleaned.lower().startswith(("tabla", "índice", "indice")):
            return cleaned[:500]
    return "Documento técnico indexado sin resumen introductorio suficiente."


def document_overview(connection, query: str) -> dict | None:
    row = find_document(connection, query)
    if not row:
        return None
    name, content, line_count = row
    headings = []
    for level, title in re.findall(r"^(#{1,6})\s+(.+?)\s*$", content, re.MULTILINE):
        clean_title = _clean_markdown(title)
        if clean_title:
            headings.append({"nivel": len(level), "titulo": clean_title})
    description = _DESCRIPTIONS.get(name) or _DESCRIPTIONS.get(
        "docs/" + Path(name).name
    ) or _first_explanatory_paragraph(content)
    return {
        "nombre": name,
        "titulo": headings[0]["titulo"] if headings else Path(name).name,
        "proposito": description,
        "lineas": int(line_count or len(content.splitlines())),
        "secciones": headings[1:31] if len(headings) > 1 else headings[:30],
        "como_usar": [
            f"lee el documento {name}",
            "siguiente (para continuar)",
            "cerrar documento (para terminar)",
        ],
    }


def format_document_overview(overview: dict) -> str:
    lines = [
        overview["titulo"],
        f"Documento: {overview['nombre']} | {overview['lineas']} líneas",
        "",
        "¿Para qué sirve?",
        overview["proposito"],
    ]
    if overview["secciones"]:
        lines.extend(["", "Contenido principal"])
        for section in overview["secciones"]:
            indent = "  " * max(0, section["nivel"] - 2)
            lines.append(f"  {indent}• {section['titulo']}")
    lines.extend([
        "", "Cómo consultarlo",
        f"  • {overview['como_usar'][0]}",
        "  • siguiente — continúa página por página",
        "  • cerrar documento — finaliza la lectura",
    ])
    return "\n".join(lines)


def catalog_quality(connection) -> dict:
    catalog = canonical_document_catalog(connection)
    missing_titles, missing_descriptions = [], []
    for item in catalog:
        row = connection.execute(
            "SELECT contenido FROM documentacion WHERE nombre=?", (item["nombre"],)
        ).fetchone()
        content = row[0] if row else ""
        if item["nombre"].lower().endswith((".md", ".txt")) and not re.search(r"^#\s+\S", content, re.MULTILINE):
            missing_titles.append(item["nombre"])
        if item["nombre"] not in _DESCRIPTIONS and len(_first_explanatory_paragraph(content)) < 45:
            missing_descriptions.append(item["nombre"])
    return {
        "documentos_unicos": len(catalog),
        "duplicados_visibles": 0,
        "sin_titulo": missing_titles,
        "sin_resumen_claro": missing_descriptions,
        "criterios": [
            "una entrada visible por contenido SHA-256",
            "ruta canónica y aliases internos",
            "título y propósito antes del contenido",
            "lectura paginada sin guardar texto en cookie",
            "evidencia histórica separada de documentación vigente",
        ],
    }
