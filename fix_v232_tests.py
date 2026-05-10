#!/usr/bin/env python3
"""Diagnostica TestImportValidado failures."""
import os, re
BASE = os.path.expanduser("~/tpv-chaquopy")
os.chdir(BASE)

# Read test file
tp = os.path.join(BASE, "tests/test_api.py")
tc = open(tp).read()

# Read app.py
ap = os.path.join(BASE, "app/src/main/python/app.py")
ac = open(ap).read()

# Read decorators
dp = os.path.join(BASE, "app/src/main/python/decorators.py")
dc = open(dp).read()

print("=== DIAGNOSTICO ===")

# Check routes
for rn in ["reconstruir-desde-productos", "importar-catalogo"]:
    pat = rf'@requiere_login.*?def.*{rn.replace("-","_")}|"/api/{rn}"'
    if re.search(pat, ac, re.DOTALL):
        print(f"  OK /api/{rn} tiene @requiere_login")
    else:
        rd = re.search(rf'"/api/{rn}"', ac)
        if rd:
            print(f"  FALTA /api/{rn} SIN @requiere_login")
        else:
            print(f"  NO ENCONTRADA /api/{rn} en app.py")

has_login = "login" in tc.lower()
print(f"  Tests usan login: {has_login}")

# Print TestImportValidado class
cm = re.search(r'class TestImportValidado.*?(?=\nclass |\Z)', tc, re.DOTALL)
if cm:
    print("\n=== TestImportValidado ===")
    print(cm.group(0)[:4000])

# Check admin_routes
arp = os.path.join(BASE, "app/src/main/python/admin_routes.py")
if os.path.exists(arp):
    arc = open(arp).read()
    ar = re.findall(r'"/api/[^"]*(?:import|reconstruir|catalogo)[^"]*"', arc, re.IGNORECASE)
    if ar:
        print("\n=== Import routes en admin_routes.py ===")
        for r in ar:
            print(f"  {r}")

# Check inventario_routes
irp = os.path.join(BASE, "app/src/main/python/inventario_routes.py")
if os.path.exists(irp):
    irc = open(irp).read()
    ir = re.findall(r'"/api/[^"]*(?:import|catalogo)[^"]*"', irc, re.IGNORECASE)
    if ir:
        print("\n=== Import routes en inventario_routes.py ===")
        for r in ir:
            print(f"  {r}")

print("\n=== FIN ===")
