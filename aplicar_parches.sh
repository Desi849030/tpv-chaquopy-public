#!/bin/bash
echo "Aplicando parches pendientes..."

# 1. SQL Injection agent.py
echo "[1/4] Parcheando agent.py..."
python3 << 'EOF'
with open('app/src/main/python/routes/agent.py', 'r') as f:
    content = f.read()

old = '''cursor = conn.execute(f"SELECT COUNT(*) as num, SUM(total) as total FROM historial_ventas {filtro} AND fecha LIKE ?", params + (f"{hoy}%",))'''
new = '''# === PARCHE SQL INJECTION ===
            if vid:
                cursor = conn.execute("SELECT COUNT(*) as num, SUM(total) as total FROM historial_ventas WHERE vendedor_id = ? AND fecha LIKE ?", (vid, f"{hoy}%"))
            else:
                cursor = conn.execute("SELECT COUNT(*) as num, SUM(total) as total FROM historial_ventas WHERE fecha LIKE ?", (f"{hoy}%",))
            # === FIN PARCHE ==='''

if old in content:
    content = content.replace(old, new)
    with open('app/src/main/python/routes/agent.py', 'w') as f:
        f.write(content)
    print("✅ agent.py parcheado")
else:
    print("⚠️  Patrón no encontrado")
EOF

# 2. SQL Injection metrics.py
echo "[2/4] Parcheando metrics.py..."
python3 << 'EOF'
with open('app/src/main/python/routes/metrics.py', 'r') as f:
    content = f.read()

old = '''cursor = conn.execute(f"SELECT COUNT(*) as num_ventas, SUM(total) as total_ingresos, SUM(cantidad) as unidades FROM historial_ventas WHERE fecha LIKE ? {filtro}", (f"{hoy}%",) + params)'''
new = '''# === PARCHE SQL INJECTION ===
        if vid:
            cursor = conn.execute("SELECT COUNT(*) as num_ventas, SUM(total) as total_ingresos, SUM(cantidad) as unidades FROM historial_ventas WHERE fecha LIKE ? AND vendedor_id = ?", (f"{hoy}%", vid))
        else:
            cursor = conn.execute("SELECT COUNT(*) as num_ventas, SUM(total) as total_ingresos, SUM(cantidad) as unidades FROM historial_ventas WHERE fecha LIKE ?", (f"{hoy}%",))
        # === FIN PARCHE ==='''

if old in content:
    content = content.replace(old, new)
    with open('app/src/main/python/routes/metrics.py', 'w') as f:
        f.write(content)
    print("✅ metrics.py parcheado")
else:
    print("⚠️  Patrón no encontrado")
EOF

# 3. IA routes
echo "[3/4] Protegiendo IA routes..."
if ! grep -q "from auth_decorator import" app/src/main/python/ia/proactive_routes.py 2>/dev/null; then
    sed -i '1i from auth_decorator import login_required' app/src/main/python/ia/proactive_routes.py
    print("✅ IA protegido"
else
    print("⚠️  Ya protegido"
fi

# 4. Verificar
echo ""
echo "[4/4] Verificación final:"
grep -c "PARCHE SQL" app/src/main/python/routes/agent.py && echo "✅ agent.py OK" || echo "❌ agent.py pendiente"
grep -c "PARCHE SQL" app/src/main/python/routes/metrics.py && echo "✅ metrics.py OK" || echo "❌ metrics.py pendiente"

echo ""
echo "Parches aplicados"
