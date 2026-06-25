"""Sistema de memoria avanzada con persistencia SQLite y caché LRU."""
from __future__ import annotations
import sqlite3, json, time, os, logging
from typing import Optional, List, Dict, Any
from collections import OrderedDict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LRUCache:
    """Caché LRU con expiración temporal."""
    
    def __init__(self, maxsize: int = 100, ttl: int = 3600):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        if time.time() - self._timestamps.get(key, 0) > self.ttl:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
            return None
        self._cache.move_to_end(key)
        return self._cache[key]
    
    def set(self, key: str, value: Any):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        self._timestamps[key] = time.time()
        if len(self._cache) > self.maxsize:
            oldest = next(iter(self._cache))
            self._cache.pop(oldest, None)
            self._timestamps.pop(oldest, None)
    
    def invalidate(self, key: str):
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self):
        self._cache.clear()
        self._timestamps.clear()


class AdvancedMemory:
    """Sistema de memoria persistente con SQLite y caché LRU."""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "..", "tpv_datos.db")
        self.db_path = db_path
        self.cache = LRUCache(maxsize=200, ttl=300)
        self._init_db()
    
    def _init_db(self):
        """Inicializar tabla de memoria."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ia_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    content TEXT NOT NULL,
                    intent TEXT,
                    entities TEXT,
                    sentiment TEXT DEFAULT 'neutral',
                    timestamp TEXT DEFAULT (datetime('now','localtime')),
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_user 
                ON ia_memory(user_id, timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_session
                ON ia_memory(session_id)
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error init memoria: {e}")
    
    def save_conversation(self, user_id: str, session_id: str, role: str, 
                          content: str, intent: str = "", entities: str = "",
                          metadata: Optional[dict] = None):
        """Guardar mensaje en memoria persistente."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """INSERT INTO ia_memory (user_id, session_id, role, content, intent, entities, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, session_id, role, content, intent, entities,
                 json.dumps(metadata) if metadata else "{}")
            )
            conn.commit()
            conn.close()
            # Invalidar caché
            self.cache.invalidate(f"history:{user_id}:{session_id}")
        except Exception as e:
            logger.error(f"Error guardando conversación: {e}")
    
    def get_conversation_history(self, user_id: str, session_id: str, 
                                  limit: int = 20) -> List[Dict]:
        """Obtener historial de conversación."""
        cache_key = f"history:{user_id}:{session_id}:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT role, content, intent, timestamp FROM ia_memory
                   WHERE user_id = ? AND session_id = ?
                   ORDER BY id DESC LIMIT ?""",
                (user_id, session_id, limit)
            )
            rows = [dict(row) for row in cursor.fetchall()]
            rows.reverse()
            conn.close()
            self.cache.set(cache_key, rows)
            return rows
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
    
    def get_user_context(self, user_id: str) -> Dict:
        """Obtener contexto del usuario (últimas interacciones)."""
        cache_key = f"context:{user_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Última intención
            cursor = conn.execute(
                """SELECT intent, content, timestamp FROM ia_memory
                   WHERE user_id = ? AND role = 'user' AND intent != ''
                   ORDER BY id DESC LIMIT 1""", (user_id,)
            )
            last_intent = dict(cursor.fetchone()) if cursor.fetchone() else {}
            
            # Intenciones frecuentes
            cursor = conn.execute(
                """SELECT intent, COUNT(*) as count FROM ia_memory
                   WHERE user_id = ? AND intent != ''
                   GROUP BY intent ORDER BY count DESC LIMIT 5""", (user_id,)
            )
            frequent_intents = [dict(r) for r in cursor.fetchall()]
            
            # Total de interacciones
            cursor = conn.execute(
                "SELECT COUNT(*) as total FROM ia_memory WHERE user_id = ?",
                (user_id,)
            )
            total = cursor.fetchone()["total"]
            
            context = {
                "user_id": user_id,
                "last_intent": last_intent.get("intent", ""),
                "last_message": last_intent.get("content", ""),
                "frequent_intents": frequent_intents,
                "total_interactions": total,
                "last_active": last_intent.get("timestamp", ""),
            }
            conn.close()
            self.cache.set(cache_key, context)
            return context
        except Exception as e:
            logger.error(f"Error obteniendo contexto: {e}")
            return {"user_id": user_id}
    
    def search_memory(self, user_id: str, query: str, limit: int = 10) -> List[Dict]:
        """Buscar en memoria por contenido."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT role, content, intent, timestamp FROM ia_memory
                   WHERE user_id = ? AND content LIKE ?
                   ORDER BY id DESC LIMIT ?""",
                (user_id, f"%{query}%", limit)
            )
            return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error buscando en memoria: {e}")
            return []
    
    def get_session_stats(self, user_id: str, session_id: str) -> Dict:
        """Estadísticas de la sesión actual."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT COUNT(*) as messages,
                          COUNT(DISTINCT intent) as intents,
                          MIN(timestamp) as started,
                          MAX(timestamp) as last
                   FROM ia_memory
                   WHERE user_id = ? AND session_id = ?""",
                (user_id, session_id)
            )
            stats = dict(cursor.fetchone())
            conn.close()
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {}
    
    def clear_user_memory(self, user_id: str):
        """Limpiar memoria de un usuario."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM ia_memory WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            self.cache.invalidate(f"context:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Error limpiando memoria: {e}")
            return False

# Singleton
advanced_memory = AdvancedMemory()
