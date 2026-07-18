from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field



@dataclass
class ValidationIssue:
    """Un problema detectado en la respuesta."""
    severity: str  # "warning" o "error"
    field: str
    message: str
    suggestion: Optional[str] = None


@dataclass

class ValidationResult:
    """Resultado completo de la validacion."""
    is_valid: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)
    corrected_data: Optional[Dict[str, Any]] = None

    def add_issue(self, severity: str, field: str, message: str, suggestion: str = None):
        self.issues.append(ValidationIssue(severity, field, message, suggestion))
        if severity == "error":
            self.is_valid = False


# ══════════════════════════════════════════════════════════
#  REGLAS DE VALIDACION
# ══════════════════════════════════════════════════════════

# Patrones de inyeccion en texto
_DANGEROUS_PATTERNS = re.compile(
    r"(?:UNION\s+SELECT|DROP\s+TABLE|INSERT\s+INTO|DELETE\s+FROM|"
    r"<script|javascript:|onerror\s*=|onload\s*=)",
    re.IGNORECASE,
)

# Montos imposibles para un TPV pequeno/mediano
_MAX_REASONABLE_SALE = 500_000.0
_MAX_REASONABLE_STOCK = 100_000.0
_MAX_REASONABLE_PRICE = 999_999.99



