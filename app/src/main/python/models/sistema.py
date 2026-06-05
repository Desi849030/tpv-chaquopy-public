from __future__ import annotations
from typing import TypedDict, Optional, List, Dict, Any

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



class Cliente(TypedDict, total=False):
    cliente_id: str
    nombre: str
    telefono: str
    email: str
    direccion: str
    rfc: str
    nota: str
    fecha_registro: str



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



class MovimientoCaja(TypedDict, total=False):
    movimiento_id: int
    tipo: str
    monto: float
    usuario_id: str
    concepto: str
    metodo_pago: str
    fecha: str



