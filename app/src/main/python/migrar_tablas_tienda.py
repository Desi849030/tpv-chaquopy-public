"""
migrar_tablas_tienda.py - Crea las 3 tablas faltantes en Supabase
tpv_tiendas, tpv_pedidos_tienda, tpv_items_pedido
"""
import json, os, sys

def obtener_supabase():
    try:
        import urllib.request
        archivos = [f for f in os.listdir(os.environ.get("TPV_FILES_DIR","."))
                    if f.endswith(".json") and "supabase" in f.lower()]
        if not archivos:
            print("[MIGRACION] No se encontro config de Supabase")
            return None, None
        with open(os.path.join(os.environ.get("TPV_FILES_DIR","."), archivos[0]), "r") as f:
            cfg = json.load(f)
        url = cfg.get("supabase_url","")
        key = cfg.get("supabase_key","")
        if not url or not key:
            print("[MIGRACION] URL o key de Supabase faltante")
            return None, None
        return url, key
    except Exception as e:
        print(f"[MIGRACION] Error: {e}")
        return None, None

def ejecutar_sql(url, key, sql):
    data = json.dumps({"sql_query": sql}).encode()
    req = urllib.request.Request(
        f"{url}/rest/v1/rpc/exec_sql",
        data=data,
        headers={
            "Content-Type": "application/json",
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Prefer": "return=minimal"
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.status
    except urllib.error.HTTPError as e:
        return e.code

def migrar():
    url, key = obtener_supabase()
    if not url:
        return

    tablas = [
        ("tpv_tiendas", """
            CREATE TABLE IF NOT EXISTS tpv_tiendas (
                id BIGSERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                emoji TEXT DEFAULT '🏪',
                admin_id TEXT,
                imagen TEXT DEFAULT '',
                creada TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(nombre)
            );
            ALTER TABLE tpv_tiendas ENABLE ROW LEVEL SECURITY;
            CREATE POLICY "Permitir todo" ON tpv_tiendas FOR ALL USING (true) WITH CHECK (true);
        """),
        ("tpv_pedidos_tienda", """
            CREATE TABLE IF NOT EXISTS tpv_pedidos_tienda (
                id BIGSERIAL PRIMARY KEY,
                cliente_id TEXT NOT NULL REFERENCES tpv_clientes(cliente_id),
                estado TEXT DEFAULT 'pendiente' CHECK (estado IN ('pendiente','aceptado','preparando','entregado','cancelado')),
                items JSONB DEFAULT '[]',
                total REAL DEFAULT 0,
                notas TEXT DEFAULT '',
                creado TIMESTAMPTZ DEFAULT NOW(),
                actualizado TIMESTAMPTZ DEFAULT NOW()
            );
            ALTER TABLE tpv_pedidos_tienda ENABLE ROW LEVEL SECURITY;
            CREATE POLICY "Permitir todo" ON tpv_pedidos_tienda FOR ALL USING (true) WITH CHECK (true);
        """),
        ("tpv_items_pedido", """
            CREATE TABLE IF NOT EXISTS tpv_items_pedido (
                id BIGSERIAL PRIMARY KEY,
                pedido_id BIGINT NOT NULL REFERENCES tpv_pedidos_tienda(id) ON DELETE CASCADE,
                producto_id TEXT NOT NULL,
                nombre TEXT NOT NULL DEFAULT '',
                cantidad INTEGER NOT NULL DEFAULT 1,
                precio_unitario REAL NOT NULL DEFAULT 0,
                subtotal REAL GENERATED ALWAYS AS (cantidad * precio_unitario) STORED
            );
            ALTER TABLE tpv_items_pedido ENABLE ROW LEVEL SECURITY;
            CREATE POLICY "Permitir todo" ON tpv_items_pedido FOR ALL USING (true) WITH CHECK (true);
        """),
    ]

    for nombre, sql in tablas:
        print(f"[MIGRACION] Creando tabla {nombre}...", end=" ")
        status = ejecutar_sql(url, key, sql)
        if status in (200, 201, 204, 409):
            print("OK")
        else:
            print(f"HTTP {status} (puede que ya exista)")

    print("[MIGRACION] Verificacion final:")
    verificar_sql = """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema='public' AND table_name LIKE 'tpv_%'
        ORDER BY table_name;
    """
    data = json.dumps({"sql_query": verificar_sql}).encode()
    req = urllib.request.Request(
        f"{url}/rest/v1/rpc/exec_sql",
        data=data,
        headers={
            "Content-Type": "application/json",
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        if isinstance(result, list):
            for r in result:
                tn = r.get("table_name","")
                print(f"  - {tn}")
            print(f"  Total: {len(result)} tablas")
        else:
            print(f"  Resultado: {result}")
    except Exception as e:
        print(f"  Error verificando: {e}")

if __name__ == "__main__":
    migrar()
