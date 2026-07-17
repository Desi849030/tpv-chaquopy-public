import sqlite3
import os
import random
from datetime import datetime, timedelta

# Ruta de la base de datos
db_path = "/data/data/com.termux/files/home/tpv-chaquopy-public/tpv_datos.db"

# Eliminar DB existente si existe
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✅ DB anterior eliminada")

# Crear conexión
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Crear tablas
print("📦 Creando tablas...")

# Tabla de productos
cursor.execute('''
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio_venta REAL DEFAULT 0,
    stock_actual INTEGER DEFAULT 0,
    categoria TEXT,
    unidad_medida TEXT DEFAULT 'ud',
    activo INTEGER DEFAULT 1
)
''')

# Tabla de categorías
cursor.execute('''
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
)
''')

# Tabla de clientes
cursor.execute('''
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT,
    telefono TEXT,
    puntos INTEGER DEFAULT 0
)
''')

# Tabla de usuarios
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    rol TEXT DEFAULT 'vendedor',
    email TEXT,
    password TEXT
)
''')

# Tabla de historial de ventas
cursor.execute('''
CREATE TABLE IF NOT EXISTS historial_ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    total REAL DEFAULT 0,
    cantidad INTEGER DEFAULT 0,
    nombre TEXT,
    vendedor_nombre TEXT,
    id_venta TEXT
)
''')

# Tabla de gastos
cursor.execute('''
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    monto REAL DEFAULT 0,
    concepto TEXT,
    categoria TEXT
)
''')

# Tabla de inventario general
cursor.execute('''
CREATE TABLE IF NOT EXISTS inventario_general (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    stock_actual INTEGER DEFAULT 0,
    stock_minimo INTEGER DEFAULT 5,
    precio_compra REAL DEFAULT 0,
    precio_venta REAL DEFAULT 0
)
''')

# Tabla de aprendizaje IA
cursor.execute('''
CREATE TABLE IF NOT EXISTS ia_learning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rol TEXT NOT NULL,
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    intent TEXT,
    hits INTEGER DEFAULT 1,
    fecha TEXT NOT NULL
)
''')

print("✅ Tablas creadas")

# Insertar categorías
categorias = ['Bebidas', 'Comidas', 'Snacks', 'Cuidado Personal', 'Limpieza']
for cat in categorias:
    cursor.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (cat,))

# Insertar productos de ejemplo
productos = [
    # Bebidas
    ("Café Americano", 2.50, 50, "Bebidas"),
    ("Café con Leche", 3.00, 40, "Bebidas"),
    ("Capuchino", 3.50, 30, "Bebidas"),
    ("Té Verde", 2.00, 60, "Bebidas"),
    ("Jugo de Naranja", 3.00, 25, "Bebidas"),
    ("Coca Cola 500ml", 1.50, 100, "Bebidas"),
    ("Agua Mineral 500ml", 1.00, 80, "Bebidas"),
    ("Limonada", 2.50, 35, "Bebidas"),
    
    # Comidas
    ("Sandwich de Jamón", 4.50, 30, "Comidas"),
    ("Sandwich de Pollo", 5.00, 25, "Comidas"),
    ("Hamburguesa Simple", 6.00, 20, "Comidas"),
    ("Hamburguesa Completa", 8.00, 15, "Comidas"),
    ("Ensalada César", 7.00, 10, "Comidas"),
    ("Pizza Margarita", 10.00, 8, "Comidas"),
    ("Pizza Pepperoni", 12.00, 5, "Comidas"),
    ("Sopa del Día", 4.00, 15, "Comidas"),
    ("Empanada de Carne", 2.50, 40, "Comidas"),
    ("Empanada de Queso", 2.50, 35, "Comidas"),
    
    # Snacks
    ("Papas Fritas", 2.00, 60, "Snacks"),
    ("Nachos con Queso", 3.50, 30, "Snacks"),
    ("Almendras Saladas", 3.00, 20, "Snacks"),
    ("Galletas", 1.50, 50, "Snacks"),
    ("Brownie", 2.50, 25, "Snacks"),
    ("Donuts", 1.50, 40, "Snacks"),
    ("Helado", 3.00, 30, "Snacks"),
    ("Palomitas", 2.00, 45, "Snacks"),
    ("Chocolate", 1.50, 60, "Snacks"),
    ("Gomitas", 1.00, 70, "Snacks"),
    
    # Cuidado Personal
    ("Shampoo", 5.00, 30, "Cuidado Personal"),
    ("Crema Dental", 3.00, 50, "Cuidado Personal"),
    ("Jabón Líquido", 2.50, 40, "Cuidado Personal"),
    ("Desodorante", 3.50, 35, "Cuidado Personal"),
    ("Crema Facial", 8.00, 20, "Cuidado Personal"),
    ("Protector Solar", 10.00, 15, "Cuidado Personal"),
    ("Colonia", 12.00, 10, "Cuidado Personal"),
    ("Cepillo de Dientes", 2.00, 60, "Cuidado Personal"),
    
    # Limpieza
    ("Detergente Líquido", 4.00, 40, "Limpieza"),
    ("Suavizante", 3.50, 35, "Limpieza"),
    ("Cloro", 2.00, 50, "Limpieza"),
    ("Limpiador Multiuso", 3.00, 45, "Limpieza"),
    ("Lavandina", 2.50, 40, "Limpieza"),
    ("Esponjas", 1.50, 80, "Limpieza"),
    ("Guantes de Limpieza", 2.00, 30, "Limpieza"),
    ("Paños de Microfibra", 3.00, 25, "Limpieza"),
]

for nombre, precio, stock, categoria in productos:
    cursor.execute("""
        INSERT INTO productos (nombre, precio_venta, stock_actual, categoria, activo)
        VALUES (?, ?, ?, ?, 1)
    """, (nombre, precio, stock, categoria))
    
    # También agregar al inventario general
    cursor.execute("""
        INSERT INTO inventario_general (nombre, stock_actual, stock_minimo, precio_venta)
        VALUES (?, ?, 5, ?)
    """, (nombre, stock, precio))

print(f"✅ {len(productos)} productos insertados")

# Insertar usuarios
usuarios = [
    ("Administrador", "admin", "admin@tpv.com", "admin123"),
    ("Desarrollador", "desarrollador", "dev@tpv.com", "dev123"),
    ("Supervisor", "supervisor", "super@tpv.com", "super123"),
    ("Vendedor", "vendedor", "vendedor@tpv.com", "vendedor123"),
]

for nombre, rol, email, password in usuarios:
    cursor.execute("""
        INSERT INTO usuarios (nombre, rol, email, password)
        VALUES (?, ?, ?, ?)
    """, (nombre, rol, email, password))

print(f"✅ {len(usuarios)} usuarios insertados")

# Insertar clientes
clientes = [
    ("Juan Pérez", "juan@email.com", "555-1111", random.randint(0, 500)),
    ("María García", "maria@email.com", "555-2222", random.randint(0, 300)),
    ("Carlos López", "carlos@email.com", "555-3333", random.randint(0, 400)),
    ("Ana Martínez", "ana@email.com", "555-4444", random.randint(0, 200)),
    ("Pedro Sánchez", "pedro@email.com", "555-5555", random.randint(0, 600)),
    ("Luis Rodríguez", "luis@email.com", "555-6666", random.randint(0, 350)),
    ("Elena Gómez", "elena@email.com", "555-7777", random.randint(0, 250)),
    ("Miguel Fernández", "miguel@email.com", "555-8888", random.randint(0, 450)),
]

for nombre, email, telefono, puntos in clientes:
    cursor.execute("""
        INSERT INTO clientes (nombre, email, telefono, puntos)
        VALUES (?, ?, ?, ?)
    """, (nombre, email, telefono, puntos))

print(f"✅ {len(clientes)} clientes insertados")

# Insertar ventas de ejemplo (últimos 7 días)
ventas = [
    ("Café Americano", 2.50, 3, "Vendedor"),
    ("Café con Leche", 3.00, 2, "Vendedor"),
    ("Capuchino", 3.50, 1, "Vendedor"),
    ("Sandwich de Jamón", 4.50, 2, "Vendedor"),
    ("Hamburguesa Simple", 6.00, 1, "Vendedor"),
    ("Papas Fritas", 2.00, 2, "Vendedor"),
    ("Coca Cola 500ml", 1.50, 4, "Vendedor"),
    ("Jugo de Naranja", 3.00, 1, "Vendedor"),
]

for nombre, precio, cantidad, vendedor in ventas:
    fecha = (datetime.now() - timedelta(days=random.randint(0, 5))).isoformat()
    total = precio * cantidad
    id_venta = f"VENTA-{random.randint(10000, 99999)}"
    cursor.execute("""
        INSERT INTO historial_ventas (fecha, total, cantidad, nombre, vendedor_nombre, id_venta)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (fecha, total, cantidad, nombre, vendedor, id_venta))

print(f"✅ {len(ventas)} ventas insertadas")

# Insertar gastos
gastos = [
    ("Luz", 50.00, "Servicios"),
    ("Agua", 30.00, "Servicios"),
    ("Internet", 40.00, "Servicios"),
    ("Proveedores", 150.00, "Compras"),
    ("Mantenimiento", 25.00, "Mantenimiento"),
    ("Publicidad", 35.00, "Marketing"),
]

for concepto, monto, categoria in gastos:
    fecha = (datetime.now() - timedelta(days=random.randint(0, 3))).isoformat()
    cursor.execute("""
        INSERT INTO gastos (fecha, monto, concepto, categoria)
        VALUES (?, ?, ?, ?)
    """, (fecha, monto, concepto, categoria))

print(f"✅ {len(gastos)} gastos insertados")

# Commit y cerrar
conn.commit()
conn.close()

print(f"\n✅ BASE DE DATOS CREADA EXITOSAMENTE")
print(f"📁 Ruta: {db_path}")
print(f"📊 {len(productos)} productos")
print(f"👥 {len(usuarios)} usuarios")
print(f"👤 {len(clientes)} clientes")
print(f"💰 {len(ventas)} ventas")
print(f"💸 {len(gastos)} gastos")
print("\n🔑 Usuarios para login:")
for nombre, rol, email, password in usuarios:
    print(f"   • {rol}: {email} / {password}")
