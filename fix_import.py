import os, re
DB = os.path.expanduser("~/tpv-chaquopy/app/src/main/python/database.py")
with open(DB,"r",encoding="utf-8") as f: c = f.read()
old = 'if not u or u["rol"] not in ("administrador","desarrollador"):'
new = 'if not u or u["rol"] not in ("administrador","desarrollador","vendedor"):'
c = c.replace(old, new)
with open(DB,"w",encoding="utf-8") as f: f.write(c)
if old in open(DB).read():
    print("ERROR: no se aplicó el fix")
else:
    print("OK Permisos de importación corregidos (vendedor incluido)")
