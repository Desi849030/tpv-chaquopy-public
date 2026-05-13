"""Facade: license_manager -> license"""
from license import (
    _LK,
    _SECRET,
    _db,
    _get_secret,
    _init_table,
    activar_licencia,
    desactivar_licencia,
    generar_device_id,
    generar_licencia,
    listar_licencias,
    requiere_licencia,
    validar_licencia,
)
