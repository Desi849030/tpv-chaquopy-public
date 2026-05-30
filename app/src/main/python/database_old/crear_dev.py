import sqlite3
import uuid
import hashlib
import os

conn = sqlite3.connect('tp.db')
c = conn.cursor()

password = "123456"
salt = os.urandom(16).hex()
hash_pw = hashlib.sha256((password + salt).encode()).hexdigest()

uid = f"user-{uuid.uuid4().hex[:8]}"

c.execute("""INSERT OR REPLACE INTO usuarios 
    (usuario_id, username, nombre, rol, password_hash, password_salt, creado_por)
    VALUES (?, ?, ?, ?, ?, ?, ?)""",
    (uid, "desarrollador", "Desarrollador Principal", "desarrollador", hash_pw, salt, "sistema"))

conn.commit()
conn.close()

print("✅ Usuario creado:")
print("   Usuario: desarrollador")
print("   Contraseña: 123456")
