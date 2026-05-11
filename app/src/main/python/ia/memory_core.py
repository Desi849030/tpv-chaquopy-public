"""memory_core.py - Extracted from memory.py"""
# -*- coding: utf-8 -*-
"""ia/memory.py - Memoria persistente para la IA del TPV
Almacena en SQLite datos clave de conversaciones:
- Preferencias de clientes
- Consultas frecuentes
- Patrones de venta
- Contexto de negocio
No afecta el rendimiento. Funciona 100% offline."""

import sqlite3, os, re, time, threading, json
from datetime import datetime, timedelta


_DB_PATH = None
_DB_LOCK = threading.Lock()


# -*- coding: utf-8 -*-
"""ia/memory.py - Memoria persistente para la IA del TPV
Almacena en SQLite datos clave de conversaciones:
- Preferencias de clientes
- Consultas frecuentes
- Patrones de venta
- Contexto de negocio
No afecta el rendimiento. Funciona 100% offline."""

import sqlite3, os, re, time, threading, json
from datetime import datetime, timedelta


_DB_PATH = None
_DB_LOCK = threading.Lock()


def _get_db():
    global _DB_PATH
    if not _DB_PATH:
        for p in ['tpv_datos.db', os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'tpv_datos.db')]:
            if os.path.exists(p):
                _DB_PATH = p
                break
    if not _DB_PATH:
        return None
    try:
        conn = sqlite3.connect(_DB_PATH, timeout=3, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def init():
    """Crea la tabla si no existe. Se llama al arrancar."""
    conn = _get_db()
    if not conn:
        return False
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS ia_memory (
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
        )''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_mem_session ON ia_memory(session_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_mem_category ON ia_memory(category)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_mem_key ON ia_memory(key)')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        try: conn.close()
        except: pass
        return False


def save(session_id='default', category='general', key='', value='',
         metadata=None, confidence=1.0, expires_days=None):
    """Guarda o actualiza un recuerdo. Upsert por (session_id, category, key)."""
    if not key or not value:
        return False
    conn = _get_db()
    if not conn:
        return False
    try:
        with _DB_LOCK:
            meta = json.dumps(metadata or {}, ensure_ascii=False)
            exp = None
            if expires_days:
                exp = (datetime.now() + timedelta(days=expires_days)).strftime('%Y-%m-%d %H:%M:%S')
            # Upsert
            existing = conn.execute(
                'SELECT id, access_count FROM ia_memory WHERE session_id=? AND category=? AND key=?',
                (session_id, category, key)).fetchone()
            if existing:
                conn.execute('''UPDATE ia_memory SET value=?, metadata=?, confidence=?,
                    access_count=access_count+1, updated_at=datetime('now','localtime'),
                    expires_at=? WHERE id=?''',
                    (str(value), meta, confidence, exp, existing['id']))
            else:
                conn.execute('''INSERT INTO ia_memory
                    (session_id, category, key, value, metadata, confidence, expires_at)
                    VALUES (?,?,?,?,?,?,?)''',
                    (session_id, category, key, str(value), meta, confidence, exp))
            conn.commit()
            conn.close()
            return True
    except Exception:
        try: conn.close()
        except: pass
        return False


def recall(session_id='default', category=None, key=None, limit=10):
    """Recupera recuerdos. Si category/key son None, devuelve todos del session."""
    conn = _get_db()
    if not conn:
        return []
    try:
        with _DB_LOCK:
            if key:
                sql = 'SELECT * FROM ia_memory WHERE session_id=? AND key=? AND (expires_at IS NULL OR expires_at > datetime("now","localtime"))'
                params = [session_id, key]
                if category:
                    sql += ' AND category=?'
                    params.append(category)
            elif category:
                sql = 'SELECT * FROM ia_memory WHERE session_id=? AND category=? AND (expires_at IS NULL OR expires_at > datetime("now","localtime")) ORDER BY updated_at DESC LIMIT ?'
                params = [session_id, category, limit]
            else:
                sql = 'SELECT * FROM ia_memory WHERE session_id=? AND (expires_at IS NULL OR expires_at > datetime("now","localtime")) ORDER BY updated_at DESC LIMIT ?'
                params = [session_id, limit]
            rows = conn.execute(sql, params).fetchall()
            # Incrementar access_count
            for r in rows:
                conn.execute('UPDATE ia_memory SET access_count=access_count+1 WHERE id=?', (r['id'],))
            conn.commit()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item['metadata'] = json.loads(item.get('metadata') or '{}')
                except Exception:
                    item['metadata'] = {}
                result.append(item)
            conn.close()
            return result
    except Exception:
        try: conn.close()
        except: pass
        return []


def search(query, session_id=None, category=None, limit=5):
    """Busca recuerdos por texto (LIKE). Búsqueda fuzzy simple."""
    conn = _get_db()
    if not conn:
        return []
    try:
        with _DB_LOCK:
            terms = query.lower().split()
            conditions = []
            params = []
            for term in terms:
                if len(term) >= 2:
                    conditions.append('(LOWER(key) LIKE ? OR LOWER(value) LIKE ?)')
                    params.extend([f'%{term}%', f'%{term}%'])
            if not conditions:
                return []
            sql = 'SELECT * FROM ia_memory WHERE ' + ' AND '.join(conditions)
            sql += ' AND (expires_at IS NULL OR expires_at > datetime("now","localtime"))'
            params_sql = list(params)
            if session_id:
                sql += ' AND session_id=?'
                params_sql.append(session_id)
            if category:
                sql += ' AND category=?'
                params_sql.append(category)
            sql += ' ORDER BY confidence DESC, access_count DESC LIMIT ?'
            params_sql.append(limit)
            rows = conn.execute(sql, params_sql).fetchall()
            conn.close()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item['metadata'] = json.loads(item.get('metadata') or '{}')
                except Exception:
                    item['metadata'] = {}
                result.append(item)
            return result
    except Exception:
        try: conn.close()
        except: pass
        return []


def forget(session_id='default', category=None, key=None):
    """Elimina recuerdos específicos o toda una categoria."""
    conn = _get_db()
    if not conn:
        return False
    try:
        with _DB_LOCK:
            if key and category:
                conn.execute('DELETE FROM ia_memory WHERE session_id=? AND category=? AND key=?',
                           (session_id, category, key))
            elif category:
                conn.execute('DELETE FROM ia_memory WHERE session_id=? AND category=?',
                           (session_id, category))
            elif key:
                conn.execute('DELETE FROM ia_memory WHERE session_id=? AND key=?',
                           (session_id, key))
            else:
                conn.execute('DELETE FROM ia_memory WHERE session_id=?', (session_id,))
            conn.commit()
            conn.close()
            return True
    except Exception:
        try: conn.close()
        except: pass
        return False


def get_summary(session_id='default'):
    """Resumen estadístico de la memoria de una sesion."""
    conn = _get_db()
    if not conn:
        return {}
    try:
        rows = conn.execute('''SELECT category, COUNT(*) as cnt,
            AVG(confidence) as avg_conf, MAX(access_count) as max_access
            FROM ia_memory WHERE session_id=?
            AND (expires_at IS NULL OR expires_at > datetime("now","localtime"))
            GROUP BY category''', (session_id,)).fetchall()
        total = conn.execute('''SELECT COUNT(*) as c FROM ia_memory WHERE session_id=?
            AND (expires_at IS NULL OR expires_at > datetime("now","localtime"))''',
            (session_id,)).fetchone()
        conn.close()
        cats = {}
        for r in rows:
            cats[r['category']] = {
                'count': r['cnt'],
                'avg_confidence': round(r['avg_conf'] or 0, 2),
                'most_accessed': r['max_access'] or 0
            }
        return {'total': total['c'] if total else 0, 'categories': cats}
    except Exception:
        try: conn.close()
        except: pass
        return {}


