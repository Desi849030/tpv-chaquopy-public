# -*- coding: utf-8 -*-
"""ia/memory_core.py - Memoria persistente para la IA del TPV.

Soporta tanto la interfaz clásica (session_id, category, key, value) como
los alias orientados a usuario (user_id, text, intent, query) con aislamiento
estricto en SQLite offline-first.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta

_DB_LOCK = threading.Lock()
_SCHEMA_SQL = """CREATE TABLE IF NOT EXISTS ia_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL DEFAULT 'default',
    category TEXT NOT NULL DEFAULT 'general',
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    confidence REAL DEFAULT 1.0,
    access_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime')),
    expires_at TEXT
)"""

__all__ = ["_get_db", "init", "save", "recall", "search", "forget", "get_summary"]


def _get_db():
    files_dir = os.environ.get("TPV_FILES_DIR", os.getcwd())
    db_path = os.path.join(files_dir, "tpv_datos.db")
    try:
        conn = sqlite3.connect(db_path, timeout=5, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute(_SCHEMA_SQL)
        return conn
    except Exception:
        return None


def init():
    """Crea la tabla e índices si no existen."""
    conn = _get_db()
    if not conn:
        return False
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_session ON ia_memory(session_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_category ON ia_memory(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_key ON ia_memory(key)")
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def save(
    session_id="default",
    category="general",
    key="",
    value="",
    metadata=None,
    confidence=1.0,
    expires_days=None,
    *,
    user_id=None,
    text=None,
    intent=None,
):
    """Guarda o actualiza un recuerdo aislado por sesión/usuario."""
    eff_session = str(user_id) if user_id is not None else str(session_id)
    eff_category = str(intent) if intent is not None else str(category)
    eff_value = text if text is not None else value
    eff_key = str(key) if key else (f"msg_{uuid.uuid4().hex[:8]}" if text is not None else "")

    if not eff_key or eff_value is None or str(eff_value) == "":
        return False
    conn = _get_db()
    if not conn:
        return False
    try:
        with _DB_LOCK:
            meta = json.dumps(metadata or {}, ensure_ascii=False)
            exp = None
            if expires_days:
                exp = (datetime.now() + timedelta(days=expires_days)).strftime("%Y-%m-%d %H:%M:%S")
            existing = conn.execute(
                "SELECT id FROM ia_memory WHERE session_id=? AND category=? AND key=?",
                (eff_session, eff_category, eff_key),
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE ia_memory SET value=?, metadata=?, confidence=?,
                    access_count=access_count+1, updated_at=datetime('now','localtime'),
                    expires_at=? WHERE id=?""",
                    (str(eff_value), meta, confidence, exp, existing["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO ia_memory
                    (session_id, category, key, value, metadata, confidence, expires_at)
                    VALUES (?,?,?,?,?,?,?)""",
                    (eff_session, eff_category, eff_key, str(eff_value), meta, confidence, exp),
                )
            conn.commit()
            return True
    except Exception:
        return False
    finally:
        conn.close()


def recall(session_id="default", category=None, key=None, limit=10, *, user_id=None):
    """Recupera recuerdos aislados del session_id / user_id."""
    eff_session = str(user_id) if user_id is not None else str(session_id)
    conn = _get_db()
    if not conn:
        return []
    try:
        with _DB_LOCK:
            if key:
                sql = (
                    "SELECT * FROM ia_memory WHERE session_id=? AND key=? "
                    "AND (expires_at IS NULL OR expires_at > datetime('now','localtime'))"
                )
                params = [eff_session, key]
                if category:
                    sql += " AND category=?"
                    params.append(category)
            elif category:
                sql = (
                    "SELECT * FROM ia_memory WHERE session_id=? AND category=? "
                    "AND (expires_at IS NULL OR expires_at > datetime('now','localtime')) "
                    "ORDER BY updated_at DESC LIMIT ?"
                )
                params = [eff_session, category, limit]
            else:
                sql = (
                    "SELECT * FROM ia_memory WHERE session_id=? "
                    "AND (expires_at IS NULL OR expires_at > datetime('now','localtime')) "
                    "ORDER BY updated_at DESC LIMIT ?"
                )
                params = [eff_session, limit]
            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                conn.execute(
                    "UPDATE ia_memory SET access_count=access_count+1 WHERE id=?",
                    (r["id"],),
                )
            conn.commit()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["metadata"] = json.loads(item.get("metadata") or "{}")
                except Exception:
                    item["metadata"] = {}
                result.append(item)
            return result
    except Exception:
        return []
    finally:
        conn.close()


def search(query="", session_id=None, category=None, limit=5, *, user_id=None):
    """Busca recuerdos por texto (LIKE) respetando el aislamiento por usuario."""
    eff_session = str(user_id) if user_id is not None else session_id
    conn = _get_db()
    if not conn:
        return []
    try:
        with _DB_LOCK:
            terms = str(query).lower().split()
            conditions = []
            params = []
            for term in terms:
                if len(term) >= 2:
                    conditions.append("(LOWER(key) LIKE ? OR LOWER(value) LIKE ?)")
                    params.extend([f"%{term}%", f"%{term}%"])
            if not conditions:
                return []
            sql = "SELECT * FROM ia_memory WHERE " + " AND ".join(conditions)
            sql += " AND (expires_at IS NULL OR expires_at > datetime('now','localtime'))"
            params_sql = list(params)
            if eff_session:
                sql += " AND session_id=?"
                params_sql.append(eff_session)
            if category:
                sql += " AND category=?"
                params_sql.append(category)
            sql += " ORDER BY confidence DESC, access_count DESC LIMIT ?"
            params_sql.append(limit)
            rows = conn.execute(sql, params_sql).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["metadata"] = json.loads(item.get("metadata") or "{}")
                except Exception:
                    item["metadata"] = {}
                result.append(item)
            return result
    except Exception:
        return []
    finally:
        conn.close()


def forget(session_id="default", category=None, key=None, *, user_id=None):
    """Elimina recuerdos específicos o todos los asociados al usuario/sesión."""
    eff_session = str(user_id) if user_id is not None else str(session_id)
    conn = _get_db()
    if not conn:
        return False
    try:
        with _DB_LOCK:
            if key and category:
                conn.execute(
                    "DELETE FROM ia_memory WHERE session_id=? AND category=? AND key=?",
                    (eff_session, category, key),
                )
            elif category:
                conn.execute(
                    "DELETE FROM ia_memory WHERE session_id=? AND category=?",
                    (eff_session, category),
                )
            elif key:
                conn.execute(
                    "DELETE FROM ia_memory WHERE session_id=? AND key=?",
                    (eff_session, key),
                )
            else:
                conn.execute("DELETE FROM ia_memory WHERE session_id=?", (eff_session,))
            conn.commit()
            return True
    except Exception:
        return False
    finally:
        conn.close()


def get_summary(session_id="default"):
    """Resumen estadístico de la memoria de una sesión."""
    conn = _get_db()
    if not conn:
        return {}
    try:
        rows = conn.execute(
            """SELECT category, COUNT(*) as cnt,
            AVG(confidence) as avg_conf, MAX(access_count) as max_access
            FROM ia_memory WHERE session_id=?
            AND (expires_at IS NULL OR expires_at > datetime('now','localtime'))
            GROUP BY category""",
            (session_id,),
        ).fetchall()
        total = conn.execute(
            """SELECT COUNT(*) as c FROM ia_memory WHERE session_id=?
            AND (expires_at IS NULL OR expires_at > datetime('now','localtime'))""",
            (session_id,),
        ).fetchone()
        cats = {}
        for r in rows:
            cats[r["category"]] = {
                "count": r["cnt"],
                "avg_confidence": round(r["avg_conf"] or 0, 2),
                "most_accessed": r["max_access"] or 0,
            }
        return {"total": total["c"] if total else 0, "categories": cats}
    except Exception:
        return {}
    finally:
        conn.close()
