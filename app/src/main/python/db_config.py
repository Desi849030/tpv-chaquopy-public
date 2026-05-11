# Re-export from split modules
from db_config_licencias import (
    crear_tablas, crear_licencia, listar_licencias,
    verificar_licencia_activa, desactivar_licencia
)
from db_config_inventario import (
    sincronizar_estado_completo, limpiar_tablas_completo,
    reconstruir_desde_productos
)
from db_config_sync import (
    cargar_estado, guardar_estado, _sincronizar_tablas_relacionales
)
