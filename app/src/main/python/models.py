"""
models.py — Definiciones de tipos (TypedDict) para todas las entidades TPV.
Industrialization v4: type safety para toda la capa de datos.
"""
from __future__ import annotations
from typing import TypedDict, Optional, List, Dict, Any


class Producto(TypedDict, total=False):
    producto_id: str
    nombre: str
    descripcion: str
    precio: float
    costo: float
    costo_unitario: float
    categoria: str
    unidad_medida: str
    en_oferta: int
    imagen: str
    activo: int
    codigo_barras: str
    stock_actual: float
    stock_minimo: float


class Categoria(TypedDict, total=False):
    categoria_id: int
    nombre: str
    descripcion: str
    activa: int


class Cliente(TypedDict, total=False):
    cliente_id: str
    nombre: str
    telefono: str
    email: str
    direccion: str
    rfc: str
    nota: str
    fecha_registro: str


class Usuario(TypedDict, total=False):
    usuario_id: str
    username: str
    nombre: str
    rol: str
    password_hash: str
    salt: str
    activo: int
    fecha_creacion: str
    ultimo_acceso: str
    pin: str


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


class InventarioGeneral(TypedDict, total=False):
    producto_id: str
    nombre: str
    stock_actual: float
    stock_minimo: float
    precio_compra: float
    precio_venta: float
    categoria: str
    unidad_medida: str
    actualizado: str


class MovimientoInventario(TypedDict, total=False):
    movimiento_id: int
    producto_id: str
    tipo: str
    cantidad: float
    stock_anterior: float
    stock_nuevo: float
    motivo: str
    usuario_id: str
    fecha: str


class MovimientoCaja(TypedDict, total=False):
    movimiento_id: int
    tipo: str
    monto: float
    usuario_id: str
    concepto: str
    metodo_pago: str
    fecha: str


class Caja(TypedDict, total=False):
    caja_id: int
    usuario_id: str
    estado: str
    monto_inicial: float
    monto_actual: float
    total_ventas: float
    total_retiros: float
    total_ingresos: float
    fecha_apertura: str
    fecha_cierre: str


class Configuracion(TypedDict, total=False):
    clave: str
    valor: str
    tipo: str
    descripcion: str


class Log(TypedDict, total=False):
    log_id: int
    usuario_id: str
    accion: str
    nivel: str
    detalles: str
    ip: str
    fecha: str


class Credito(TypedDict, total=False):
    credito_id: int
    cliente_id: str
    venta_id: str
    monto: float
    saldo_pendiente: float
    estado: str
    fecha_vencimiento: str
    fecha_creacion: str


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
