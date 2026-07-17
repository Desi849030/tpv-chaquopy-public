"""
ia/result_cache.py — Caché TTL para resultados de db_utils.q().
Evita consultas repetitivas a SQLite en la misma conversación.

Inspirado en: free-code/src/utils/toolResultStorage.ts
"""

from __future__ import annotations
import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    """Entrada en la caché."""
    key: str
    value: Any
    created_at: float
    ttl: float
    hit_count: int = 0
    size_bytes: int = 0


class ResultCache:
    """
    Caché LRU con TTL para resultados de consultas.

    Uso:
        cache = ResultCache(max_size=100, default_ttl=30.0)

        # Guardar
        cache.set("SELECT * FROM productos WHERE id=1", rows)

        # Leer
        rows = cache.get("SELECT * FROM productos WHERE id=1")
        if rows is None:
            rows = db_utils.q("SELECT * FROM productos WHERE id=1")
            cache.set("SELECT * FROM productos WHERE id=1", rows)

        # Envolver db_utils.q
        cached_q = cache.wrap_query(db_utils.q)
        rows = cached_q("SELECT * FROM productos WHERE categoria='bebidas'")
    """

    def __init__(
        self,
        max_size: int = 100,
        default_ttl: float = 30.0,
        max_memory_bytes: int = 5 * 1024 * 1024,  # 5MB
    ):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.max_memory_bytes = max_memory_bytes
        self._lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "sets": 0,
        }

    def _make_key(self, query: str, params: tuple = ()) -> str:
        """Genera una clave hash para la consulta."""
        raw = f"{query}|{params}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, query: str, params: tuple = ()) -> Any | None:
        """
        Obtiene un resultado cacheado.

        Returns:
            El resultado cacheado o None si expiró/no existe.
        """
        key = self._make_key(query, params)
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None

            # Verificar TTL
            if time.time() - entry.created_at > entry.ttl:
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            # Mover al final (LRU)
            self._cache.move_to_end(key)
            entry.hit_count += 1
            self._stats["hits"] += 1
            return entry.value

    def set(
        self,
        query: str,
        value: Any,
        params: tuple = (),
        ttl: float | None = None,
    ) -> None:
        """
        Guarda un resultado en caché.

        Args:
            query: La consulta SQL.
            value: El resultado a cachear.
            params: Parámetros de la consulta.
            ttl: Time-to-live en segundos (usa default_ttl si None).
        """
        key = self._make_key(query, params)
        ttl = ttl if ttl is not None else self.default_ttl

        # Estimar tamaño
        try:
            size = len(str(value))
        except Exception:
            size = 0

        with self._lock:
            # Evict si excede tamaño máximo
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self._stats["evictions"] += 1

            # Evict por memoria si es necesario
            total_size = sum(e.size_bytes for e in self._cache.values())
            while total_size + size > self.max_memory_bytes and self._cache:
                evicted = self._cache.popitem(last=False)
                total_size -= evicted[1].size_bytes
                self._stats["evictions"] += 1

            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl,
                size_bytes=size,
            )
            self._stats["sets"] += 1

    def invalidate(self, query: str | None = None, params: tuple = ()) -> int:
        """
        Invalida entradas de la caché.

        Args:
            query: Si None, limpia toda la caché. Si str, invalida esa clave.

        Returns:
            Número de entradas invalidadas.
        """
        with self._lock:
            if query is None:
                count = len(self._cache)
                self._cache.clear()
                return count
            key = self._make_key(query, params)
            if key in self._cache:
                del self._cache[key]
                return 1
            return 0

    def invalidate_pattern(self, table_name: str) -> int:
        """
        Invalida todas las entradas que contengan un nombre de tabla.

        Útil después de INSERT/UPDATE/DELETE en esa tabla.
        """
        # Como las keys son hashes, no podemos buscar por patrón.
        # Solución: limpiar toda la caché (conservador pero seguro).
        # En el futuro se puede guardar el query original también.
        return self.invalidate()

    def wrap_query(self, query_fn):
        """
        Envuelve una función de consulta con caché.

        Uso:
            cached_q = cache.wrap_query(db_utils.q)
            rows = cached_q("SELECT * FROM productos WHERE id=?", (1,))
        """
        def cached_wrapper(query: str, *args, **kwargs):
            params = args if args else kwargs.get("params", ())
            if isinstance(params, (list, tuple)):
                params = tuple(params)
            else:
                params = (params,)

            # Solo cachear SELECTs
            query_stripped = query.strip().upper()
            if not query_stripped.startswith("SELECT"):
                # Si no es SELECT, invalidar cache (la BD cambió)
                self.invalidate()
                return query_fn(query, *args, **kwargs)

            cached = self.get(query, params)
            if cached is not None:
                return cached

            result = query_fn(query, *args, **kwargs)
            self.set(query, result, params)
            return result

        # Adjuntar referencia al cache para control manual
        cached_wrapper._cache = self
        cached_wrapper._original = query_fn
        return cached_wrapper

    def get_stats(self) -> dict:
        """Estadísticas de la caché."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0.0
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(hit_rate, 1),
            "evictions": self._stats["evictions"],
            "total_sets": self._stats["sets"],
            "current_size": len(self._cache),
            "max_size": self.max_size,
        }

    def clear(self) -> None:
        """Limpia toda la caché."""
        with self._lock:
            self._cache.clear()


# Singleton
_cache: ResultCache | None = None


def get_cache() -> ResultCache:
    """Devuelve la caché singleton."""
    global _cache
    if _cache is None:
        _cache = ResultCache()
    return _cache


def reset_cache() -> None:
    """Resetea la caché (útil para tests)."""
    global _cache
    _cache = ResultCache()
