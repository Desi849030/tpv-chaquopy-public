from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .models import (
    ValidationResult,
    _DANGEROUS_PATTERNS,
    _MAX_REASONABLE_PRICE,
    _MAX_REASONABLE_SALE,
    _MAX_REASONABLE_STOCK,
)


def validate_financial_response(data: Dict[str, Any]) -> ValidationResult:
    """Valida datos financieros: ventas, totales, ganancias."""
    result = ValidationResult()

    # Validar totales de venta
    total = data.get("total") or data.get("total_venta") or data.get("monto")
    if total is not None:
        try:
            total_val = float(total)
            if total_val < 0:
                result.add_issue(
                    "error", "total",
                    f"El total no puede ser negativo: {total_val}",
                    suggestion=str(abs(total_val)),
                )
            elif total_val > _MAX_REASONABLE_SALE:
                result.add_issue(
                    "warning", "total",
                    f"El total es inusualmente alto: {total_val}",
                    suggestion="Verificar que no haya error en la cantidad o precio",
                )
        except (ValueError, TypeError):
            result.add_issue("error", "total", f"Total no es un numero valido: {total}")

    # Validar ganancia
    ganancia = data.get("ganancia") or data.get("profit") or data.get("utilidad")
    if ganancia is not None:
        try:
            gan_val = float(ganancia)
            # La ganancia puede ser negativa, pero si las ventas son positivas
            # y la ganancia es extremadamente negativa, es sospechoso
            if gan_val < -_MAX_REASONABLE_SALE:
                result.add_issue(
                    "warning", "ganancia",
                    f"La ganancia es muy negativa: {gan_val}",
                    suggestion="Verificar costos y descuentos aplicados",
                )
        except (ValueError, TypeError):
            pass

    # Validar porcentaje de descuento
    descuento = data.get("descuento") or data.get("descuento_pct")
    if descuento is not None:
        try:
            desc_val = float(descuento)
            if desc_val < 0:
                result.add_issue(
                    "error", "descuento",
                    f"El descuento no puede ser negativo: {desc_val}%",
                    suggestion="0",
                )
            elif desc_val > 100:
                result.add_issue(
                    "error", "descuento",
                    f"El descuento no puede superar 100%: {desc_val}%",
                    suggestion="100",
                )
        except (ValueError, TypeError):
            pass

    return result



def validate_inventory_response(data: Dict[str, Any]) -> ValidationResult:
    """Valida datos de inventario: stock, precios, cantidades."""
    result = ValidationResult()

    # Validar stock
    stock = data.get("stock") or data.get("stock_actual") or data.get("cantidad")
    if stock is not None:
        try:
            stock_val = float(stock)
            if stock_val < 0:
                result.add_issue(
                    "error", "stock",
                    f"El stock no puede ser negativo: {stock_val}",
                    suggestion="0",
                )
            elif stock_val > _MAX_REASONABLE_STOCK:
                result.add_issue(
                    "warning", "stock",
                    f"El stock es inusualmente alto: {stock_val}",
                    suggestion="Verificar si es un error de entrada",
                )
        except (ValueError, TypeError):
            pass

    # Validar precio
    precio = data.get("precio") or data.get("precio_venta") or data.get("price")
    if precio is not None:
        try:
            precio_val = float(precio)
            if precio_val < 0:
                result.add_issue(
                    "error", "precio",
                    f"El precio no puede ser negativo: {precio_val}",
                    suggestion="0.0",
                )
            elif precio_val > _MAX_REASONABLE_PRICE:
                result.add_issue(
                    "warning", "precio",
                    f"El precio es muy alto: {precio_val}",
                    suggestion="Verificar que no haya error de decimal",
                )
        except (ValueError, TypeError):
            result.add_issue("error", "precio", f"Precio no es un numero: {precio}")

    # Validar codigo de producto
    prod_id = data.get("producto_id") or data.get("id") or data.get("codigo")
    if prod_id is not None and isinstance(prod_id, str):
        if len(prod_id.strip()) == 0:
            result.add_issue("error", "producto_id", "El ID de producto esta vacio")

    return result



def validate_text_response(text: str) -> ValidationResult:
    """Valida texto de respuesta antes de mostrarlo."""
    result = ValidationResult()

    if not text or not text.strip():
        result.add_issue("error", "texto", "La respuesta esta vacia")
        return result

    # Detectar patrones peligrosos
    dangerous = _DANGEROUS_PATTERNS.search(text)
    if dangerous:
        result.add_issue(
            "error", "texto",
            f"Patron peligroso detectado en la respuesta: {dangerous.group(0)}",
            suggestion="El texto fue sanitizado",
        )

    # Detectar posibles fugas de informacion interna
    internal_patterns = [
        (r"Traceback \(most recent call", "Traceback de Python expuesto"),
        (r"File .*/(app|src)/", "Ruta de archivo interno expuesta"),
        (r"sqlite3\.OperationalError", "Error de base de datos expuesto"),
        (r"password|secret|token.*[=:]", "Posible credencial expuesta"),
    ]
    for pattern, desc in internal_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            result.add_issue(
                "warning", "texto",
                f"Posible fuga de informacion: {desc}",
                suggestion="Sanitizar antes de enviar al usuario",
            )

    # Detectar respuestas muy cortas que podrian ser errores
    if len(text.strip()) < 5 and not text.strip().startswith(("$", "0")):
        result.add_issue(
            "warning", "texto",
            "La respuesta es muy corta, podria ser un error",
            suggestion="Generar una respuesta mas descriptiva",
        )

    return result



def validate_response(
    data: Any,
    response_type: str = "auto",
) -> ValidationResult:
    """
    Valida una respuesta completa del agente.
    response_type: "financial", "inventory", "text", "auto" (detecta automaticamente)
    """
    if response_type == "auto":
        if isinstance(data, dict):
            keys_lower = {k.lower() for k in data.keys()}
            if keys_lower & {"total", "ganancia", "venta", "precio", "subtotal", "impuesto"}:
                if keys_lower & {"stock", "inventario", "cantidad"}:
                    response_type = "inventory"
                else:
                    response_type = "financial"
            elif keys_lower & {"stock", "inventario", "producto"}:
                response_type = "inventory"
            else:
                response_type = "financial"
        elif isinstance(data, str):
            response_type = "text"
        else:
            return ValidationResult()

    if response_type == "financial":
        return validate_financial_response(data)
    elif response_type == "inventory":
        return validate_inventory_response(data)
    elif response_type == "text":
        return validate_text_response(data)

    return ValidationResult()



def format_validation_message(result: ValidationResult) -> str:
    """Genera un mensaje legible con los problemas encontrados."""
    if result.is_valid and not result.issues:
        return ""
    lines = []
    for issue in result.issues:
        icon = "[!]" if issue.severity == "error" else "[?]"
        lines.append(f"  {icon} {issue.field}: {issue.message}")
        if issue.suggestion:
            lines.append(f"      -> {issue.suggestion}")
    return "Problemas detectados en la respuesta:\n" + "\n".join(lines)

