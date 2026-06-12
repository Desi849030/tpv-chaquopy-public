"""
agent_state.py — Memoria persistente de estado del agente IA.
Implementa gobernanza de memoria: guarda metas, pasos completados,
contexto y resultados entre sesiones.

Tabla SQLite: agent_sessions
  - session_id: ID unico de sesion del agente
  - user_id: ID del usuario
  - current_goal: Meta/objetivo actual del agente
  - current_step: Paso actual en el plan
  - total_steps: Total de pasos en el plan
  - completed_steps: JSON con pasos completados y sus resultados
  - context: JSON con contexto adicional (filtro activo, parametros, etc.)
  - status: active, completed, paused, cancelled
  - created_at, updated_at: Timestamps

Industrialization v5 — Agentic AI Layer
"""
from __future__ import annotations
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


def _get_db_path() -> str:
    """Obtiene la ruta de la base de datos."""
    from db_connection import DB_PATH
    return DB_PATH


def _ensure_table():
    """Crea la tabla agent_sessions si no existe."""
    import sqlite3
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            current_goal TEXT NOT NULL DEFAULT '',
            current_step INTEGER DEFAULT 0,
            total_steps INTEGER DEFAULT 0,
            completed_steps TEXT DEFAULT '{}',
            context TEXT DEFAULT '{}',
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def create_session(
    session_id: str,
    user_id: str,
    goal: str,
    total_steps: int = 0,
) -> Dict[str, Any]:
    """Crea una nueva sesion de agente con una meta."""
    _ensure_table()
    import sqlite3
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO agent_sessions
               (session_id, user_id, current_goal, current_step, total_steps,
                completed_steps, context, status, created_at, updated_at)
               VALUES (?, ?, ?, 0, ?, '{}', '{}', 'active', ?, ?)""",
            (session_id, user_id, goal, total_steps, now, now),
        )
        conn.commit()
        return {"ok": True, "session_id": session_id, "goal": goal}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene una sesion de agente por ID."""
    _ensure_table()
    import sqlite3
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agent_sessions WHERE session_id=?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    result = dict(row)
    try:
        result["completed_steps"] = json.loads(result.get("completed_steps") or "{}")
    except (json.JSONDecodeError, TypeError):
        result["completed_steps"] = {}
    try:
        result["context"] = json.loads(result.get("context") or "{}")
    except (json.JSONDecodeError, TypeError):
        result["context"] = {}
    return result


def update_step(
    session_id: str,
    step_index: int,
    step_result: Dict[str, Any],
    context_update: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Actualiza el paso actual y guarda el resultado del paso anterior."""
    _ensure_table()
    import sqlite3
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session = get_session(session_id)
    if not session:
        return {"ok": False, "error": "Sesion no encontrada"}
    completed = session["completed_steps"]
    if step_index > 0:
        prev_step_key = f"step_{step_index - 1}"
        completed[prev_step_key] = step_result
    ctx = session["context"]
    if context_update:
        ctx.update(context_update)
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE agent_sessions
               SET current_step=?, completed_steps=?, context=?, updated_at=?
               WHERE session_id=?""",
            (step_index, json.dumps(completed, ensure_ascii=False),
             json.dumps(ctx, ensure_ascii=False), now, session_id),
        )
        conn.commit()
        return {"ok": True, "current_step": step_index}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def complete_session(session_id: str, final_result: Optional[Dict] = None) -> Dict[str, Any]:
    """Marca una sesion como completada con el resultado final."""
    _ensure_table()
    import sqlite3
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session = get_session(session_id)
    if not session:
        return {"ok": False, "error": "Sesion no encontrada"}
    ctx = session["context"]
    if final_result:
        ctx["final_result"] = final_result
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE agent_sessions SET status='completed', context=?, updated_at=?
               WHERE session_id=?""",
            (json.dumps(ctx, ensure_ascii=False), now, session_id),
        )
        conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def get_active_sessions(user_id: str) -> List[Dict[str, Any]]:
    """Obtiene todas las sesiones activas de un usuario."""
    _ensure_table()
    import sqlite3
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM agent_sessions WHERE user_id=? AND status='active' ORDER BY updated_at DESC",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    results = []
    for row in rows:
        r = dict(row)
        try:
            r["completed_steps"] = json.loads(r.get("completed_steps") or "{}")
        except (json.JSONDecodeError, TypeError):
            r["completed_steps"] = {}
        results.append(r)
    return results


def cancel_session(session_id: str) -> Dict[str, Any]:
    """Cancela una sesion de agente."""
    _ensure_table()
    import sqlite3
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE agent_sessions SET status='cancelled', updated_at=? WHERE session_id=?",
            (now, session_id),
        )
        conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()
