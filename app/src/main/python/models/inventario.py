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



