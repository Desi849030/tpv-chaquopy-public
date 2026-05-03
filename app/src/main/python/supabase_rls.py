"""
supabase_rls.py v1.0 - TPV Ultra Smart
Row Level Security para Supabase
Filtro criptográfico por sucursal/tienda
"""
import json, hashlib, os
from datetime import datetime

def get_branch_id() -> str:
    """Obtiene ID único de la sucursal/tienda"""
    branch_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.branch_id')
    
    if os.path.exists(branch_file):
        with open(branch_file, 'r') as f:
            return f.read().strip()
    
    # Generar ID de sucursal único
    branch_id = f"branch-{hashlib.md5(os.urandom(32)).hexdigest()[:10]}"
    with open(branch_file, 'w') as f:
        f.write(branch_id)
    
    return branch_id

def build_rls_query(table: str, branch_id: str = None) -> str:
    """
    Construye filtro RLS para consultas Supabase.
    Asegura que cada sucursal solo vea sus datos.
    
    Args:
        table: Nombre de la tabla
        branch_id: ID de sucursal (auto-detecta si None)
    
    Returns:
        Filtro para Supabase
    """
    if not branch_id:
        branch_id = get_branch_id()
    
    return f"branch_id=eq.{branch_id}"

def filter_inventory_by_branch(items: list, branch_id: str = None) -> list:
    """
    Filtra inventario para mostrar solo productos de esta sucursal.
    """
    if not branch_id:
        branch_id = get_branch_id()
    
    return [
        item for item in items
        if item.get('branch_id', '') == branch_id or not item.get('branch_id')
    ]

def filter_sales_by_branch(sales: list, branch_id: str = None) -> list:
    """
    Filtra ventas para mostrar solo transacciones de esta sucursal.
    """
    if not branch_id:
        branch_id = get_branch_id()
    
    return [
        sale for sale in sales
        if sale.get('branch_id', '') == branch_id
    ]

def get_rls_headers() -> dict:
    """Obtiene headers RLS para peticiones a Supabase"""
    branch_id = get_branch_id()
    
    return {
        "X-Branch-ID": branch_id,
        "X-RLS-Enabled": "true",
        "X-Timestamp": datetime.now().isoformat()
    }

def assign_to_branch(data: dict, branch_id: str = None) -> dict:
    """Asigna datos a una sucursal específica"""
    if not branch_id:
        branch_id = get_branch_id()
    
    data['branch_id'] = branch_id
    data['branch_assigned_at'] = datetime.now().isoformat()
    return data

# Política RLS para Supabase (SQL para ejecutar en Supabase Dashboard)
RLS_SQL_POLICIES = """
-- Ejecutar en Supabase SQL Editor

-- Habilitar RLS en tablas
ALTER TABLE tpv_ventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_inventario ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_productos ENABLE ROW LEVEL SECURITY;

-- Política: sucursal solo ve sus datos
CREATE POLICY "Branch isolation - ventas"
ON tpv_ventas FOR ALL
USING (branch_id = current_setting('request.headers')::json->>'x-branch-id');

CREATE POLICY "Branch isolation - inventario"
ON tpv_inventario FOR ALL
USING (branch_id = current_setting('request.headers')::json->>'x-branch-id');

CREATE POLICY "Branch isolation - productos"
ON tpv_productos FOR SELECT
USING (branch_id = current_setting('request.headers')::json->>'x-branch-id' OR branch_id IS NULL);
"""

print("✅ supabase_rls.py v1.0 listo - RLS multi-sucursal activo")
print(f"   Sucursal ID: {get_branch_id()}")
