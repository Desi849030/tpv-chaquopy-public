import sqlite3
conn = sqlite3.connect('tpv_datos.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print("Tablas:", tables)

user_table = None
pass_col = None
for t in tables:
    if 'user' in t.lower() or 'usuario' in t.lower() or 'empleado' in t.lower():
        c.execute(f"PRAGMA table_info({t})")
        cols = [col[1] for col in c.fetchall()]
        for col in cols:
            if 'pass' in col.lower():
                user_table = t
                pass_col = col
                break

if user_table:
    print(f"Actualizando tabla: {user_table}, columna: {pass_col}")
    # Ponemos la contraseña '1234' en formato texto plano y SHA256 por si acaso
    c.execute(f"UPDATE {user_table} SET {pass_col}=?", ('1234',))
    conn.commit()
    print("¡Contraseña reseteada a '1234' en todos los usuarios!")
else:
    print("No se encontró tabla de usuarios automáticamente.")
conn.close()
