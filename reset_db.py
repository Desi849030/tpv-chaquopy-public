import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('tpv_datos.db')
c = conn.cursor()

# Buscar tablas
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]

# Buscar la tabla de usuarios
for t in tables:
    if 'user' in t.lower() or 'usuario' in t.lower() or 'empleado' in t.lower():
        c.execute(f"PRAGMA table_info({t})")
        cols = [col[1] for col in c.fetchall()]
        pass_col = None
        for col in cols:
            if 'pass' in col.lower():
                pass_col = col
                break
        
        if pass_col:
            # Generar hash profesional para la contraseña '1234'
            hash_pass = generate_password_hash('1234')
            c.execute(f"UPDATE {t} SET {pass_col}=?", (hash_pass,))
            conn.commit()
            print(f"¡Contraseña reseteada a '1234' en la tabla {t}!")
            break
conn.close()
