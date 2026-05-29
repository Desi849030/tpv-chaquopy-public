import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Directorio base: {base_dir}")
print(f"\nEstructura de directorios:")
for root, dirs, files in os.walk(base_dir):
    level = root.replace(base_dir, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files[:5]:  # Mostrar solo 5 archivos por directorio
        print(f'{subindent}{file}')
    if len(files) > 5:
        print(f'{subindent}... y {len(files)-5} más')

print(f"\nVerificando accesibilidad:")
for folder in ['templates', 'static']:
    path = os.path.join(base_dir, folder)
    if os.path.exists(path):
        print(f"✓ {folder} existe")
        try:
            os.listdir(path)
            print(f"  ✓ Accesible")
        except:
            print(f"  ✗ NO accesible (permisos)")
    else:
        print(f"✗ {folder} NO existe")
