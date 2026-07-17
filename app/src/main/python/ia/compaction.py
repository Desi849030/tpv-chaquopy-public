"""
ia/compaction.py — Compacción de contexto por reglas.
Reduce el historial de conversación manteniendo la información esencial.

Inspirado en: free-code/src/commands/compact/compact.ts
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    """Representa un mensaje en el historial."""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class CompactionResult:
    """Resultado de la compacción."""
    original_count: int
    compacted_count: int
    reduction_pct: float
    preserved_summary: str
    messages: list[Message]


# Patrones de mensajes que se pueden resumir/eliminar
SUMMARIZABLE_PATTERNS = [
    (r"^(s[ií]|no|ok|vale|bueno|bien|gracias|perfecto|entendido|claro|aja)[\s.!]*$", "afirmacion"),
    (r"^(no\s+(sé|se|entiendo|entiende|comprendo)|no\s+(puedo|puedes))[\s.!]*$", "negacion"),
    (r"^(un\s+momento|espera|dame|déjame)\s+(pensar|verificar|buscar|revisar).*[\s.!]*$", "espera"),
]

ESSENTIAL_PATTERNS = [
    r"\b(crear|nuevo|agregar|eliminar|borrar|modificar|editar|cambiar)\b",
    r"\b(total|subtotal|precio|costo|monto|pago|cobro)\b",
    r"\b(cliente|producto|venta|factura|ticket|recibo)\b",
    r"\bstock|inventario|existencia|cantidad\b",
    r"\d+\.\d{2}",  # Montos con decimales
    r"\d{4,}",  # IDs o números largos
]


class ConversationCompactor:
    """
    Compactor de historial de conversación.

    Reglas:
    1. Eliminar mensajes vacíos o muy cortos (< 3 tokens)
    2. Fusionar mensajes consecutivos del mismo rol
    3. Resumir mensajes de confirmación ("sí", "ok", "no", etc.)
    4. Preservar siempre: mensajes con números, menciones a productos/clientes,
       y los últimos N mensajes del usuario y asistente
    5. Generar un resumen compacto del contexto eliminado
    """

    def __init__(
        self,
        max_messages: int = 50,
        keep_recent: int = 10,
        min_tokens: int = 3,
    ):
        self.max_messages = max_messages
        self.keep_recent = keep_recent
        self.min_tokens = min_tokens

    def _tokenize_simple(self, text: str) -> list[str]:
        """Tokenización simple por espacios (sin dependencias externas)."""
        return text.split()

    def _is_summarizable(self, msg: Message) -> tuple[bool, str]:
        """Verifica si un mensaje puede ser resumido."""
        content = msg.content.strip()
        for pattern, category in SUMMARIZABLE_PATTERNS:
            if re.match(pattern, content, re.IGNORECASE):
                return True, category
        return False, ""

    def _is_essential(self, msg: Message) -> bool:
        """Verifica si un mensaje contiene información esencial."""
        if msg.role == "system":
            return True
        content = msg.content
        for pattern in ESSENTIAL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        # Mensajes largos probablemente tienen información útil
        tokens = self._tokenize_simple(content)
        if len(tokens) > 20:
            return True
        return False

    def _extract_facts(self, messages: list[Message]) -> list[str]:
        """Extrae hechos clave de los mensajes a eliminar."""
        facts = []
        for msg in messages:
            # Buscar números con contexto (montos, cantidades, IDs)
            money_matches = re.findall(
                r"([\w\s]{0,30}?\d+[\.,]\d{2})", msg.content
            )
            for m in money_matches:
                facts.append(f"- Monto/cantidad mencionado: {m.strip()}")

            # Buscar nombres de productos/clientes (palabras con mayúsculas)
            proper_nouns = re.findall(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b", msg.content)
            for noun in proper_nouns:
                if len(noun) > 3 and noun.lower() not in (
                    "el", "la", "los", "las", "un", "una", "del", "con",
                    "para", "por", "que", "como", "pero", "más", "esto",
                ):
                    facts.append(f"- Entidad mencionada: {noun}")
        return facts

    def compact(self, messages: list[Message]) -> CompactionResult:
        """
        Compacta la lista de mensajes.

        Args:
            messages: Lista de Message del historial completo.

        Returns:
            CompactionResult con el historial compactado.
        """
        original_count = len(messages)

        if original_count <= self.max_messages:
            return CompactionResult(
                original_count=original_count,
                compacted_count=original_count,
                reduction_pct=0.0,
                preserved_summary="",
                messages=messages,
            )

        # Separar: system messages siempre se preservan
        system_msgs = [m for m in messages if m.role == "system"]
        conversation = [m for m in messages if m.role != "system"]

        # Tomar los N más recientes
        recent = conversation[-self.keep_recent:] if len(conversation) > self.keep_recent else conversation
        older = conversation[:-self.keep_recent] if len(conversation) > self.keep_recent else []

        # De los antiguos, preservar los esenciales
        essential = [m for m in older if self._is_essential(m)]
        summarizable = [m for m in older if not self._is_essential(m)]

        # Extraer hechos de los mensajes resumibles
        facts = self._extract_facts(summarizable)

        # Generar resumen
        summary_parts = []
        cat_counts: dict[str, int] = {}
        for msg in summarizable:
            _, cat = self._is_summarizable(msg)
            if cat:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
        if cat_counts:
            parts = [f"{v} {k}" for k, v in cat_counts.items()]
            summary_parts.append("Mensajes breves: " + ", ".join(parts))
        if facts:
            summary_parts.extend(facts[:10])  # Máximo 10 hechos
        preserved_summary = "\n".join(summary_parts) if summary_parts else ""

        # Componer resultado: system + esenciales antiguos + resumen + recientes
        compacted = list(system_msgs) + essential
        if preserved_summary:
            compacted.append(Message(
                role="system",
                content=f"[Contexto previo compactado]\n{preserved_summary}",
                metadata={"compacted": True, "removed_count": len(summarizable)},
            ))
        compacted.extend(recent)

        # Fusionar mensajes consecutivos del mismo rol
        compacted = self._merge_consecutive(compacted)

        compacted_count = len(compacted)
        reduction = round((1 - compacted_count / original_count) * 100, 1) if original_count > 0 else 0.0

        return CompactionResult(
            original_count=original_count,
            compacted_count=compacted_count,
            reduction_pct=reduction,
            preserved_summary=preserved_summary,
            messages=compacted,
        )

    def _merge_consecutive(self, messages: list[Message]) -> list[Message]:
        """Fusiona mensajes consecutivos del mismo rol."""
        if not messages:
            return messages
        merged = [messages[0]]
        for msg in messages[1:]:
            if msg.role == merged[-1].role and msg.role != "system":
                merged[-1] = Message(
                    role=msg.role,
                    content=merged[-1].content + "\n" + msg.content,
                    timestamp=merged[-1].timestamp,
                    metadata={**merged[-1].metadata, **msg.metadata, "merged": True},
                )
            else:
                merged.append(msg)
        return merged


def compact_history(messages: list[Message], max_messages: int = 50) -> CompactionResult:
    """Función de conveniencia para compactar historial."""
    compactor = ConversationCompactor(max_messages=max_messages)
    return compactor.compact(messages)
