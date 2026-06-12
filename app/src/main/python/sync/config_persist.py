"""config_persist.py - Extracted from config.py"""
"""
╔══════════════════════════════════════════════════════════════╗
║   supabase_sync.py  —  TPV ULTRA SMART  v6.1               ║
║   Sincronización dinámica + Historial Diario                ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import os
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ══════════════════════════════════════════════════════════════
#  PERSISTENCIA DE CONFIGURACION A DISCO
# ══════════════════════════════════════════════════════════════
_CONFIG_FILE = os.path.join(os.environ.get("TPV_FILES_DIR", os.getcwd()), ".supabase_config.json")

def _cargar_config_desde_archivo():
    """Carga config persistida desde JSON. Retorna dict o None."""
    try:
        if os.path.exists(_CONFIG_FILE):
            with open(_CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception:  # noqa: broad-except - graceful degradation
        pass
    return None

def _guardar_config_a_archivo():
    """Persiste la config actual a JSON en disco."""
    try:
        data = {
            "url": SUPABASE_CONFIG.get("url", ""),
            "anon_key": SUPABASE_CONFIG.get("anon_key", ""),
        }
        with open(_CONFIG_FILE, 'w') as f:
            json.dump(data, f)
        return True
    except Exception:
        return False

# ══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════
# Valores por defecto (se sobreescriben con lo persistido en disco)
_DEFAULT_URL = os.environ.get("SUPABASE_URL", "")
_DEFAULT_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

# Intentar cargar config persistida desde disco
_persisted = _cargar_config_desde_archivo()
_URL = _persisted["url"] if _persisted and _persisted.get("url") else _DEFAULT_URL
_KEY = _persisted["anon_key"] if _persisted and _persisted.get("anon_key") else _DEFAULT_KEY

SUPABASE_CONFIG = {
    "url":            _URL,
    "anon_key":       _KEY,
    "tabla_estado":         "tpv_estado",
    "tabla_usuarios":       "tpv_usuarios",
    "tabla_clientes":       "tpv_clientes",
    "tabla_ventas":         "tpv_ventas_dia",
    "tabla_productos":      "tpv_productos",
    "tabla_stock":          "tpv_stock",
    "tabla_gastos":         "tpv_gastos_dia",
    "tabla_historial":      "tpv_historial_diario",
    "tabla_tiendas":        "tpv_tiendas",
    "tabla_pedidos":        "tpv_pedidos_tienda",
    "tabla_items_pedido":   "tpv_items_pedido",
    "tabla_cierres_caja":  "tpv_cierres_caja",
    "tabla_inventarios":   "tpv_inventarios",
    "tabla_ventas_hist":   "tpv_ventas",
    "tabla_pedidos_all":   "tpv_pedidos",
    "registro_id":          1,
}

# SUPABASE_OK movido a config_supabase.py

# ══════════════════════════════════════════════════════════════
#  SQL DINÁMICO PARA CADA TABLA
# ══════════════════════════════════════════════════════════════
TABLAS_SQL = {
    "tpv_estado": """
        CREATE TABLE IF NOT EXISTS tpv_estado (
            id          SERIAL PRIMARY KEY,
            dispositivo TEXT        NOT NULL DEFAULT 'principal',
            estado      JSONB       NOT NULL DEFAULT '{}',
            actualizado TIMESTAMPTZ DEFAULT NOW()
        );
        INSERT INTO tpv_estado (dispositivo, estado)
        VALUES ('principal', '{}') ON CONFLICT DO NOTHING;
    """,
    "tpv_usuarios": """
        CREATE TABLE IF NOT EXISTS tpv_usuarios (
            usuario_id    TEXT PRIMARY KEY,
            username      TEXT        NOT NULL UNIQUE,
            nombre        TEXT        NOT NULL,
            rol           TEXT        NOT NULL,
            password_hash TEXT        NOT NULL,
            password_salt TEXT        NOT NULL,
            activo        BOOLEAN     DEFAULT TRUE,
            ultimo_acceso TIMESTAMPTZ,
            creado        TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_tpv_usuarios_rol ON tpv_usuarios(rol);
    """,
    "tpv_clientes": """
        CREATE TABLE IF NOT EXISTS tpv_clientes (
            cliente_id    TEXT PRIMARY KEY,
            nombre        TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            telefono      TEXT    DEFAULT '',
            password_hash TEXT    NOT NULL,
            password_salt TEXT    NOT NULL,
            activo        BOOLEAN DEFAULT TRUE,
            creado        TIMESTAMPTZ DEFAULT NOW()
        );
    """,
    "tpv_ventas_dia": """
        CREATE TABLE IF NOT EXISTS tpv_ventas_dia (
            venta_id        TEXT PRIMARY KEY,
            producto_id     TEXT,
            nombre          TEXT,
            cantidad        NUMERIC DEFAULT 0,
            precio_unit     NUMERIC DEFAULT 0,
            total           NUMERIC DEFAULT 0,
            metodo_pago     TEXT    DEFAULT 'efectivo',
            vendedor_id     TEXT,
            vendedor_nombre TEXT,
            fecha           TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_tpv_ventas_fecha    ON tpv_ventas_dia(fecha);
        CREATE INDEX IF NOT EXISTS idx_tpv_ventas_vendedor ON tpv_ventas_dia(vendedor_id);
    """,
    "tpv_productos": """
        CREATE TABLE IF NOT EXISTS tpv_productos (
            producto_id   TEXT PRIMARY KEY,
            nombre        TEXT    NOT NULL,
            precio        NUMERIC DEFAULT 0,
            costo         NUMERIC DEFAULT 0,
            categoria     TEXT    DEFAULT 'General',
            unidad_medida TEXT    DEFAULT 'C/U',
            en_oferta     BOOLEAN DEFAULT FALSE,
            activo        BOOLEAN DEFAULT TRUE,
            actualizado   TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_tpv_productos_cat ON tpv_productos(categoria, activo);
    """,
    "tpv_stock": """
        CREATE TABLE IF NOT EXISTS tpv_stock (
            producto_id   TEXT PRIMARY KEY,
            nombre        TEXT,
            stock_actual  NUMERIC DEFAULT 0,
            precio_venta  NUMERIC DEFAULT 0,
            categoria     TEXT    DEFAULT 'General',
            actualizado   TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_tpv_stock_cat ON tpv_stock(categoria);
    """,
    "tpv_gastos_dia": """
        CREATE TABLE IF NOT EXISTS tpv_gastos_dia (
            id          SERIAL PRIMARY KEY,
            descripcion TEXT    NOT NULL,
            monto       NUMERIC NOT NULL DEFAULT 0,
            categoria   TEXT    DEFAULT 'General',
            fecha       TIMESTAMPTZ DEFAULT NOW(),
            admin_id    TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_tpv_gastos_fecha ON tpv_gastos_dia(fecha);
    """,
    "tpv_historial_diario": """
        CREATE TABLE IF NOT EXISTS tpv_historial_diario (
            id                SERIAL PRIMARY KEY,
            fecha             DATE        NOT NULL UNIQUE,
            total_ventas      NUMERIC     DEFAULT 0,
            num_transacciones INTEGER     DEFAULT 0,
            productos_activos INTEGER     DEFAULT 0,
            inventario_items  INTEGER     DEFAULT 0,
            ventas_data       JSONB       DEFAULT '[]',
            inventario_data   JSONB       DEFAULT '[]',
            config_snapshot   JSONB       DEFAULT '{}',
            ts_guardado       TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_tpv_hist_fecha ON tpv_historial_diario(fecha DESC);
    """,
    "tpv_tiendas": """
        CREATE TABLE IF NOT EXISTS tpv_tiendas (
            tienda_id     TEXT PRIMARY KEY,
            nombre        TEXT    NOT NULL,
            direccion     TEXT    DEFAULT '',
            telefono      TEXT    DEFAULT '',
            email         TEXT    DEFAULT '',
            activa        BOOLEAN DEFAULT TRUE,
            creada        TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_tpv_tiendas_activa ON tpv_tiendas(activa);
    """,
    "tpv_pedidos_tienda": """
        CREATE TABLE IF NOT EXISTS tpv_pedidos_tienda (
            pedido_id     TEXT PRIMARY KEY,
            cliente_id    TEXT,
            cliente_nombre TEXT   DEFAULT '',
            tienda_id     TEXT,
            items         JSONB   DEFAULT '[]',
            total         NUMERIC DEFAULT 0,
            estado        TEXT    DEFAULT 'pendiente',
            metodo_pago   TEXT    DEFAULT 'efectivo',
            fecha         TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_tpv_pedidos_fecha ON tpv_pedidos_tienda(fecha);
        CREATE INDEX IF NOT EXISTS idx_tpv_pedidos_estado ON tpv_pedidos_tienda(estado);
    """,
    "tpv_items_pedido": """
        CREATE TABLE IF NOT EXISTS tpv_items_pedido (
            item_id       TEXT PRIMARY KEY,
            pedido_id     TEXT,
            producto_id   TEXT,
            nombre        TEXT    DEFAULT '',
            cantidad      NUMERIC DEFAULT 0,
            precio_unit   NUMERIC DEFAULT 0,
            subtotal      NUMERIC DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_tpv_items_pedido_id ON tpv_items_pedido(pedido_id);
    """,
}

# SQL completo de todas las tablas (para copiar al portapapeles)
SQL_COMPLETO = "\n".join(TABLAS_SQL.values()) + """
-- ════ RLS ════
ALTER TABLE tpv_estado          ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_usuarios        ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_clientes        ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_ventas_dia      ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_productos       ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_stock           ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_gastos_dia      ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_historial_diario ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_tiendas           ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_pedidos_tienda    ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpv_items_pedido      ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN CREATE POLICY "backend_all_estado" ON tpv_estado FOR ALL USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE POLICY "backend_all_usuarios" ON tpv_usuarios FOR ALL USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE POLICY "backend_all_clientes" ON tpv_clientes FOR ALL USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE POLICY "backend_all_ventas" ON tpv_ventas_dia FOR ALL USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE POLICY "backend_all_productos" ON tpv_productos FOR ALL USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE POLICY "backend_all_stock" ON tpv_stock FOR ALL USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE POLICY "backend_all_gastos" ON tpv_gastos_dia FOR ALL USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE POLICY "backend_all_historial" ON tpv_historial_diario FOR ALL USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE POLICY "backend_all_tiendas" ON tpv_tiendas FOR ALL USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE POLICY "backend_all_pedidos" ON tpv_pedidos_tienda FOR ALL USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE POLICY "backend_all_items_pedido" ON tpv_items_pedido FOR ALL USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
"""

# ══════════════════════════════════════════════════════════════
#  VERIFICACIÓN DE CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════
