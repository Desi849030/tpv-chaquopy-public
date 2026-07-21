"""Synchronize curated project documentation into SQLite for offline IA use."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

_LOG = logging.getLogger(__name__)
_DOCUMENT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".toml"}
_MAX_DOCUMENT_BYTES = 1_000_000
_MODULE_DIR = Path(__file__).resolve().parent
_PACKAGED_DIR = _MODULE_DIR / "knowledge"
_PACKAGED_REPOSITORY_DIR = _PACKAGED_DIR / "repository"
_REPOSITORY_ROOT = _MODULE_DIR.parents[3]

# Public name -> candidates in priority order. Repository files are richer in
# Termux/desktop; packaged copies guarantee a useful offline baseline in APK.
_DOCUMENTS = {
    "README.md": (_REPOSITORY_ROOT / "README.md", _PACKAGED_DIR / "PROJECT_OVERVIEW.md"),
    "DEVELOPER_GUIDE.md": (
        _REPOSITORY_ROOT / "docs" / "DEVELOPER_GUIDE.md",
        _PACKAGED_DIR / "DEVELOPER_GUIDE.md",
    ),
    "ROADMAP_10_10.md": (
        _REPOSITORY_ROOT / "docs" / "ROADMAP_10_10.md",
        _PACKAGED_DIR / "ROADMAP_10_10.md",
    ),
    "ARCHITECTURE.md": (_REPOSITORY_ROOT / "docs" / "ARCHITECTURE.md",),
    "API_REFERENCE.md": (_REPOSITORY_ROOT / "docs" / "API_REFERENCE.md",),
    "BACKEND_MAP.md": (_REPOSITORY_ROOT / "docs" / "BACKEND_MAP.md",),
    "DATABASE_SCHEMA.md": (_REPOSITORY_ROOT / "docs" / "DATABASE_SCHEMA.md",),
    "CONTRIBUTING.md": (_REPOSITORY_ROOT / "docs" / "CONTRIBUTING.md",),
    "CHECKLIST_RELEASE.md": (_REPOSITORY_ROOT / "docs" / "CHECKLIST_RELEASE.md",),
    "CHANGELOG.md": (_REPOSITORY_ROOT / "CHANGELOG.md",),
    "LICENSE": (_REPOSITORY_ROOT / "LICENSE",),
}


def _first_readable(candidates: Iterable[Path]) -> str | None:
    for path in candidates:
        try:
            if path.is_file():
                return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            _LOG.warning("Could not read documentation file %s", path, exc_info=True)
    return None


def _repository_documents() -> Iterable[tuple[str, Path]]:
    """Yield every text document available in a full repository checkout."""
    if not (_REPOSITORY_ROOT / ".git").exists():
        return
    roots = [
        path for path in _REPOSITORY_ROOT.iterdir()
        if path.is_file() and (path.suffix.lower() in _DOCUMENT_SUFFIXES or path.name == "LICENSE")
    ]
    roots.extend(
        path for path in (_REPOSITORY_ROOT / "docs").rglob("*")
        if path.is_file() and path.suffix.lower() in _DOCUMENT_SUFFIXES
    )
    for path in sorted(roots):
        try:
            if path.stat().st_size <= _MAX_DOCUMENT_BYTES:
                yield path.relative_to(_REPOSITORY_ROOT).as_posix(), path
        except OSError:
            continue


def _packaged_repository_documents() -> Iterable[tuple[str, Path]]:
    """Yield the complete documentation copied into the APK at build time."""
    if not _PACKAGED_REPOSITORY_DIR.is_dir():
        return
    for path in sorted(_PACKAGED_REPOSITORY_DIR.rglob("*")):
        try:
            if (
                path.is_file()
                and (path.suffix.lower() in _DOCUMENT_SUFFIXES or path.name == "LICENSE")
                and path.stat().st_size <= _MAX_DOCUMENT_BYTES
            ):
                yield path.relative_to(_PACKAGED_REPOSITORY_DIR).as_posix(), path
        except OSError:
            continue


def _upsert_document(connection, name: str, content: str) -> None:
    connection.execute(
        """
        INSERT INTO documentacion (nombre, contenido, lineas, actualizado)
        VALUES (?, ?, ?, datetime('now','localtime'))
        ON CONFLICT(nombre) DO UPDATE SET
            contenido=excluded.contenido,
            lineas=excluded.lineas,
            actualizado=excluded.actualizado
        """,
        (name, content, len(content.splitlines())),
    )


def sync_documentation(connection) -> int:
    """Synchronize curated APK docs and every document in a full checkout."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS documentacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            contenido TEXT NOT NULL,
            lineas INTEGER NOT NULL DEFAULT 0,
            actualizado TEXT DEFAULT (datetime('now','localtime'))
        )
        """
    )
    synchronized_names: set[str] = set()
    for name, candidates in _DOCUMENTS.items():
        content = _first_readable(candidates)
        if content is None:
            continue
        _upsert_document(connection, name, content)
        synchronized_names.add(name)

    for source in (_packaged_repository_documents(), _repository_documents()):
        for name, path in source:
            content = _first_readable((path,))
            if content is None:
                continue
            _upsert_document(connection, name, content)
            synchronized_names.add(name)

    connection.commit()
    return len(synchronized_names)


def find_document(connection, query: str):
    """Resolve a natural-language document request to one SQLite row."""
    normalized = " ".join(str(query or "").lower().split())
    if not normalized:
        return None
    rows = connection.execute(
        "SELECT nombre, contenido, lineas FROM documentacion ORDER BY length(nombre), nombre"
    ).fetchall()
    exact_candidates = []
    fuzzy_candidates = []
    for row in rows:
        name = row[0]
        name_lower = name.lower()
        basename = Path(name).name.lower()
        stem = Path(name).stem.lower().replace("_", " ").replace("-", " ")
        if normalized in {name_lower, basename, stem}:
            exact_candidates.append(row)
        elif name_lower in normalized or basename in normalized or (len(stem) >= 4 and stem in normalized):
            fuzzy_candidates.append(row)
    return (exact_candidates or fuzzy_candidates or [None])[0]


def available_document_names(connection) -> list[str]:
    """Return synchronized document names in display order."""
    rows = connection.execute(
        "SELECT nombre FROM documentacion ORDER BY nombre"
    ).fetchall()
    return [row[0] for row in rows]
