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


def cleanup(expired_only=True, max_age_days=90):
    """Limpia recuerdos expirados o antiguos."""
    conn = _get_db()
    if not conn:
        return 0
    try:
        with _DB_LOCK:
            if expired_only:
                n = conn.execute('''DELETE FROM ia_memory WHERE expires_at IS NOT NULL
                    AND expires_at <= datetime("now","localtime")''').rowcount
            else:
                n = conn.execute('''DELETE FROM ia_memory WHERE updated_at < datetime("now","localtime",?)
                    AND confidence < 0.5''', (f'-{max_age_days} days',)).rowcount
            conn.commit()
            conn.close()
            return n
    except Exception:
        try: conn.close()
        except: pass
        return 0


def extract_and_save(session_id, user_text, intent, response_summary, role='cliente'):
    """Extrae datos clave de una conversacion y los guarda automaticamente.
    Se llama despues de cada respuesta de la IA."""
    if not user_text or len(user_text) < 3:
        return
    t = user_text.lower().strip()
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Detectar preferencias de producto ("me gusta X", "busco X", "quiero X")
    pref_patterns = [
        (r'(?:me gusta|prefiero|quiero|busco|necesito|interesa)\s+(.+?)(?:\.|$|,)', 'preferencia'),
        (r'(?:cuanto cuesta|precio de|precio del?)\s+(.+?)(?:\.|$|\?)', 'consulta_precio'),
        (r'(?:hay|tiene|disponible)\s+(.+?)(?:\?|$)', 'consulta_stock'),
    ]
    for pattern, cat in pref_patterns:
        m = re.search(pattern, t)
        if m:
            val = m.group(1).strip()[:200]
            if len(val) >= 3:
                save(session_id, cat, val[:80], val,
                     metadata={'source': 'auto', 'role': role, 'intent': intent},
                     confidence=0.7, expires_days=30)

    # Guardar consulta frecuente (si se repite, confidence sube)
    existing = search(t[:50], session_id=session_id, category='consulta_frecuente', limit=1)
    if existing:
        conf = min(existing[0].get('confidence', 0.7) + 0.1, 1.0)
        count = existing[0].get('access_count', 1) + 1
        save(session_id, 'consulta_frecuente', t[:80],
             response_summary[:200] if response_summary else t[:200],
             metadata={'count': count, 'source': 'auto', 'role': role},
             confidence=conf, expires_days=60)
    elif intent and intent not in ('chat', 'saludo', 'despedida', 'ayuda'):
        save(session_id, 'consulta_frecuente', t[:80],
             response_summary[:200] if response_summary else t[:200],
             metadata={'count': 1, 'source': 'auto', 'role': role},
             confidence=0.5, expires_days=60)

    # Detectar nombre de cliente si lo menciona
    if role == 'cliente':
        name_match = re.search(r'(?:me llamo|soy|mi nombre es)\s+(\w+)', t)
        if name_match:
            save(session_id, 'dato_cliente', 'nombre', name_match.group(1),
                 confidence=0.9, expires_days=120)


def get_enriched_context(session_id, user_text):
    """Recupera contexto relevante para enriquecer la respuesta de la IA.
    Se llama antes de procesar una pregunta."""
    t = user_text.lower().strip()
    context = {
        'memories': [],
        'frequent_queries': [],
        'preferences': [],
        'client_data': {}
    }

    # Buscar preferencias relacionadas
    for term in t.split():
        if len(term) >= 3:
            prefs = search(term, session_id=session_id, category='preferencia', limit=3)
            context['preferences'].extend(prefs)

    # Deduplicar preferencias
    seen = set()
    unique_prefs = []
    for p in context['preferences']:
        k = p.get('key', '')
        if k not in seen:
            seen.add(k)
            unique_prefs.append(p)
    context['preferences'] = unique_prefs[:5]

    # Datos del cliente
    client = recall(session_id, category='dato_cliente', limit=10)
    if client:
        for c in client:
            context['client_data'][c['key']] = c['value']

    # Consultas frecuentes recientes
    freq = recall(session_id, category='consulta_frecuente', limit=3)
    context['frequent_queries'] = freq

    # Recuerdos generales recientes
    general = recall(session_id, category='general', limit=5)
    context['memories'] = general

    return context


# Inicializar al importar
_init_done = init()
if _init_done:
    print("[ia/memory.py] Memoria persistente inicializada")
else:
    print("[ia/memory.py] WARN: No se pudo inicializar BD de memoria")
