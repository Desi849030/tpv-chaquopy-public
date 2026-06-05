"""memory_advanced.py - Extracted from memory.py"""
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


from ia.memory_core import _get_db, init, save, search, recall, forget, get_summary

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
