from __future__ import annotations
from typing import TypedDict, Optional, List, Dict, Any

class Venta(TypedDict, total=False):
    venta_id: str
    cliente_id: str
    usuario_id: str
    total: float
    subtotal: float
    descuento: float
    impuesto: float
    metodo_pago: str
    estado: str
    referencia: str
    nota: str
    fecha: str



class DetalleVenta(TypedDict, total=False):
    detalle_id: int
    venta_id: str
    producto_id: str
    nombre_producto: str
    cantidad: float
    precio_unitario: float
    descuento: float
    subtotal: float



class Corte(TypedDict, total=False):
    corte_id: int
    usuario_id: str
    fecha_inicio: str
    fecha_fin: str
    ventas_total: float
    ventas_efectivo: float
    ventas_tarjeta: float
    ventas_credito: float
    retiros: float
    ingresos: float
    saldo_esperado: float
    saldo_real: float
    diferencia: float



class Credito(TypedDict, total=False):
    credito_id: int
    cliente_id: str
    venta_id: str
    monto: float
    saldo_pendiente: float
    estado: str
    fecha_vencimiento: str
    fecha_creacion: str



class APIResponse(TypedDict, total=False):
    ok: bool
    data: Optional[Any]
    error: Optional[str]
    mensaje: Optional[str]



class PaginatedResponse(APIResponse, total=False):
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int



class ValidationResult(TypedDict, total=False):
    valido: bool
    total_filas: int
    total_errores: int
    total_validos: int
    errores: List[Dict[str, Any]]
    advertencias: List[str]

