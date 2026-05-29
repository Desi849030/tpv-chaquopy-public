"""
Simulador de Interfaz Web del POS
Simula lo que verías en el navegador después de login + activar terminal
"""

import os
import sqlite3
from datetime import datetime

DB_FILE = 'data/tpv.db'

# Colores para terminal (simula UI)
class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def header(titulo):
    print(f"\n{Color.CYAN}{'='*50}")
    print(f"  {titulo}")
    print(f"{'='*50}{Color.END}")

def card(titulo, descripcion, icono="📌"):
    print(f"\n  {Color.BOLD}{icono} {titulo}{Color.END}")
    print(f"  {Color.CYAN}   {descripcion}{Color.END}")
    print(f"  {'─'*40}")

def mostrar_menu_principal(usuario):
    header(f"TERMINAL ACTIVO - {usuario['nombre']} ({usuario['rol']})")
    print(f"\n  {Color.GREEN}✓ Terminal activada - {datetime.now().strftime('%H:%M:%S')}{Color.END}")
    
    print(f"\n  {Color.BOLD}MENÚ PRINCIPAL{Color.END}")
    
    cards = [
        ("🛒", "Nueva Venta", "Registrar venta a cliente"),
        ("📦", "Productos", "Catálogo y stock"),
        ("👥", "Clientes", "Gestionar clientes"),
        ("💰", "Corte de Caja", "Reporte de ventas del día"),
        ("📊", "Estadísticas", "Ventas, productos más vendidos"),
        ("⚙️", "Configuración", "Ajustes del sistema"),
        ("📝", "Logs", "Historial de actividad"),
        ("🚪", "Cerrar Sesión", "Salir y bloquear terminal"),
    ]
    
    for icono, titulo, desc in cards:
        card(titulo, desc, icono)
    
    return cards

def submenu_ventas():
    header("🛒 NUEVA VENTA")
    
    print(f"\n  {Color.BOLD}SUBMENÚ VENTAS{Color.END}")
    
    opciones = [
        ("📝", "Venta Rápida", "Sin cliente registrado"),
        ("👤", "Venta con Cliente", "Buscar o crear cliente"),
        ("📋", "Ver Ventas del Día", "Listado de ventas"),
        ("🔍", "Buscar Venta", "Por número o fecha"),
        ("❌", "Cancelar Venta", "Anular venta existente"),
        ("↩️", "Volver", "Regresar al menú principal"),
    ]
    
    for icono, titulo, desc in opciones:
        card(titulo, desc, icono)
    
    return opciones

def submenu_productos():
    header("📦 PRODUCTOS")
    
    # Obtener productos de la BD
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE activo = 1 ORDER BY nombre")
    productos = cursor.fetchall()
    
    print(f"\n  {Color.BOLD}CATÁLOGO DE PRODUCTOS ({len(productos)} items){Color.END}")
    
    print(f"\n  {'ID':<4} {'Código':<10} {'Nombre':<25} {'Precio':>10} {'Stock':>8}")
    print(f"  {'─'*60}")
    
    for p in productos:
        stock_color = Color.GREEN if p['stock_actual'] > p['stock_minimo'] else Color.WARNING
        print(f"  {p['id']:<4} {p['codigo']:<10} {p['nombre']:<25} ${p['precio']:>8.2f} {stock_color}{p['stock_actual']:>6}{Color.END}")
    
    conn.close()
    
    print(f"\n  {Color.BOLD}OPCIONES{Color.END}")
    opciones = [
        ("➕", "Agregar Producto", "Nuevo producto al catálogo"),
        ("✏️", "Editar Producto", "Modificar precio, stock, etc"),
        ("📥", "Entrada de Stock", "Aumentar inventario"),
        ("🗑️", "Eliminar Producto", "Desactivar producto"),
        ("📂", "Categorías", "Gestionar categorías"),
        ("🔍", "Buscar Producto", "Por nombre o código"),
        ("↩️", "Volver", "Regresar al menú principal"),
    ]
    
    for icono, titulo, desc in opciones:
        card(titulo, desc, icono)
    
    return opciones

def submenu_clientes():
    header("👥 CLIENTES")
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes ORDER BY nombre")
    clientes = cursor.fetchall()
    
    print(f"\n  {Color.BOLD}LISTA DE CLIENTES ({len(clientes)} registros){Color.END}")
    
    print(f"\n  {'ID':<4} {'Nombre':<25} {'Email':<25} {'Teléfono':<12}")
    print(f"  {'─'*70}")
    
    for c in clientes:
        print(f"  {c['id']:<4} {c['nombre']:<25} {c['email'] or 'N/A':<25} {c['telefono'] or 'N/A':<12}")
    
    conn.close()
    
    print(f"\n  {Color.BOLD}OPCIONES{Color.END}")
    opciones = [
        ("➕", "Nuevo Cliente", "Registrar cliente"),
        ("✏️", "Editar Cliente", "Modificar datos"),
        ("🔍", "Buscar Cliente", "Por nombre, email o teléfono"),
        ("🗑️", "Eliminar Cliente", "Borrar registro"),
        ("↩️", "Volver", "Regresar al menú principal"),
    ]
    
    for icono, titulo, desc in opciones:
        card(titulo, desc, icono)
    
    return opciones

def submenu_corte_caja():
    header("💰 CORTE DE CAJA")
    
    hoy = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as suma FROM ventas WHERE DATE(fecha) = ?", (hoy,))
    resultado = cursor.fetchone()
    
    cursor.execute("SELECT metodo_pago, COUNT(*) as count, SUM(total) as total FROM ventas WHERE DATE(fecha) = ? GROUP BY metodo_pago", (hoy,))
    metodos = cursor.fetchall()
    
    print(f"\n  {Color.BOLD}REPORTE DEL DÍA: {hoy}{Color.END}")
    print(f"\n  {'─'*40}")
    print(f"  Total de ventas: {Color.BOLD}{resultado['total']}{Color.END}")
    print(f"  Monto total:     {Color.WARNING}${resultado['suma']:,.2f}{Color.END}")
    
    if metodos:
        print(f"\n  {Color.BOLD}POR MÉTODO DE PAGO:{Color.END}")
        for m in metodos:
            print(f"    {m['metodo_pago']}: {m['count']} ventas - ${m['total']:,.2f}")
    
    conn.close()
    
    print(f"\n  {Color.BOLD}OPCIONES{Color.END}")
    opciones = [
        ("📄", "Imprimir Reporte", "Generar ticket de corte"),
        ("📅", "Corte por Fecha", "Ver otro día"),
        ("📊", "Resumen Mensual", "Totales del mes"),
        ("↩️", "Volver", "Regresar al menú principal"),
    ]
    
    for icono, titulo, desc in opciones:
        card(titulo, desc, icono)
    
    return opciones

def submenu_estadisticas():
    header("📊 ESTADÍSTICAS")
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Productos más vendidos
    cursor.execute("""
        SELECT p.nombre, SUM(dv.cantidad) as vendidos
        FROM detalle_ventas dv
        JOIN productos p ON dv.producto_id = p.id
        GROUP BY p.id
        ORDER BY vendidos DESC
        LIMIT 5
    """)
    top_productos = cursor.fetchall()
    
    # Total de ventas
    cursor.execute("SELECT COUNT(*) as total FROM ventas")
    total_ventas = cursor.fetchone()['total']
    
    cursor.execute("SELECT COALESCE(SUM(total), 0) as suma FROM ventas")
    suma_ventas = cursor.fetchone()['suma']
    
    print(f"\n  {Color.BOLD}RESUMEN GENERAL{Color.END}")
    print(f"\n  {'─'*40}")
    print(f"  Total ventas: {total_ventas}")
    print(f"  Monto total:  ${suma_ventas:,.2f}")
    
    if top_productos:
        print(f"\n  {Color.BOLD}TOP 5 PRODUCTOS MÁS VENDIDOS:{Color.END}")
        for i, p in enumerate(top_productos, 1):
            print(f"    {i}. {p['nombre']} ({p['vendidos']} unidades)")
    
    conn.close()
    
    print(f"\n  {Color.BOLD}OPCIONES{Color.END}")
    opciones = [
        ("📈", "Ventas por Período", "Filtrar por fecha"),
        ("🏆", "Productos más vendidos", "Ranking completo"),
        ("💳", "Métodos de pago", "Distribución"),
        ("↩️", "Volver", "Regresar al menú principal"),
    ]
    
    for icono, titulo, desc in opciones:
        card(titulo, desc, icono)
    
    return opciones

def submenu_configuracion():
    header("⚙️ CONFIGURACIÓN")
    
    print(f"\n  {Color.BOLD}OPCIONES{Color.END}")
    opciones = [
        ("👤", "Usuarios", "Gestionar usuarios y roles"),
        ("🏪", "Datos del Negocio", "Nombre, dirección, teléfono"),
        ("🖨️", "Impresora", "Configurar impresora de tickets"),
        ("💾", "Base de Datos", "Respaldar o restaurar"),
        ("🔒", "Licencia", "Estado de la licencia"),
        ("↩️", "Volver", "Regresar al menú principal"),
    ]
    
    for icono, titulo, desc in opciones:
        card(titulo, desc, icono)
    
    return opciones

def mostrar_logs():
    header("📝 LOGS DEL SISTEMA")
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 20")
    logs = cursor.fetchall()
    
    print(f"\n  {'ID':<4} {'Nivel':<10} {'Módulo':<15} {'Mensaje':<30} {'Fecha'}")
    print(f"  {'─'*80}")
    
    for log in logs:
        nivel_color = Color.GREEN if log['nivel'] == 'INFO' else Color.WARNING if log['nivel'] == 'WARNING' else Color.FAIL
        print(f"  {log['id']:<4} {nivel_color}{log['nivel']:<10}{Color.END} {log['modulo']:<15} {log['mensaje'][:30]:<30} {log['creado_en']}")
    
    conn.close()

# ========== SIMULACIÓN COMPLETA ==========

if __name__ == "__main__":
    print(f"\n{Color.BLUE}{'*'*50}")
    print(f"  SIMULADOR DE INTERFAZ POS - TPV ANDROID")
    print(f"{'*'*50}{Color.END}")

    # Simular login
    usuario = {
        'id': 1,
        'username': 'desarrollador',
        'nombre': 'Desarrollador',
        'rol': 'desarrollador'
    }

    input(f"\n  {Color.BOLD}Presiona ENTER para activar terminal...{Color.END}")

    # Menú principal
    while True:
        mostrar_menu_principal(usuario)
        
        opcion = input(f"\n  {Color.BOLD}Selecciona una opción (1-8):{Color.END} ").strip()
        
        if opcion == '1':
            submenu_ventas()
            input(f"\n  Presiona ENTER para volver...")
        elif opcion == '2':
            submenu_productos()
            input(f"\n  Presiona ENTER para volver...")
        elif opcion == '3':
            submenu_clientes()
            input(f"\n  Presiona ENTER para volver...")
        elif opcion == '4':
            submenu_corte_caja()
            input(f"\n  Presiona ENTER para volver...")
        elif opcion == '5':
            submenu_estadisticas()
            input(f"\n  Presiona ENTER para volver...")
        elif opcion == '6':
            submenu_configuracion()
            input(f"\n  Presiona ENTER para volver...")
        elif opcion == '7':
            mostrar_logs()
            input(f"\n  Presiona ENTER para volver...")
        elif opcion == '8':
            print(f"\n  {Color.GREEN}✓ Sesión cerrada. Terminal bloqueada.{Color.END}")
            break
        else:
            print(f"  {Color.FAIL}Opción no válida{Color.END}")
