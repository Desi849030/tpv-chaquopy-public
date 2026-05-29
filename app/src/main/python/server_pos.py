#!/usr/bin/env python3
"""
POS TPV - Servidor Web Profesional
Sistema completo de punto de venta con todas las funcionalidades
"""

import http.server
import json
import sqlite3
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import hashlib
import secrets

DB_FILE = 'data/tpv.db'

# ========== FUNCIONES DE BASE DE DATOS ==========

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def buscar_tabla(tabla, campos="*", where=None, params=(), orden="id", limite=100):
    conn = get_conn()
    query = f"SELECT {campos} FROM {tabla}"
    if where:
        query += f" WHERE {where}"
    query += f" ORDER BY {orden} LIMIT {limite}"
    cursor = conn.execute(query, params)
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados

def insertar(tabla, datos):
    conn = get_conn()
    campos = ', '.join(datos.keys())
    placeholders = ', '.join(['?'] * len(datos))
    query = f"INSERT INTO {tabla} ({campos}) VALUES ({placeholders})"
    conn.execute(query, list(datos.values()))
    conn.commit()
    id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return id

def actualizar(tabla, id, datos):
    conn = get_conn()
    campos = ', '.join([f"{k} = ?" for k in datos.keys()])
    valores = list(datos.values()) + [id]
    conn.execute(f"UPDATE {tabla} SET {campos} WHERE id = ?", valores)
    conn.commit()
    conn.close()

def eliminar(tabla, id):
    conn = get_conn()
    conn.execute(f"DELETE FROM {tabla} WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# ========== HTML TEMPLATES ==========

def get_html(title, content, usuario=None):
    nombre = usuario['nombre'] if usuario else 'Desarrollador'
    rol = usuario.get('rol', 'admin') if usuario else 'admin'
    
    return f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - POS TPV</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; min-height: 100vh; }}
        
        /* Header */
        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }}
        .header h1 {{ font-size: 1.4rem; display: flex; align-items: center; gap: 10px; }}
        .header h1 i {{ color: #3498db; }}
        .user-info {{ display: flex; align-items: center; gap: 15px; }}
        .user-info .badge {{ background: #3498db; padding: 5px 12px; border-radius: 20px; font-size: 0.85rem; }}
        .logout-btn {{ background: #e74c3c; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; }}
        .logout-btn:hover {{ background: #c0392b; }}
        
        /* Status bar */
        .status-bar {{ background: #27ae60; color: white; padding: 8px 25px; font-size: 0.9rem; display: flex; justify-content: space-between; }}
        
        /* Sidebar */
        .layout {{ display: flex; min-height: calc(100vh - 110px); }}
        .sidebar {{ width: 250px; background: #2c3e50; padding: 20px 0; overflow-y: auto; }}
        .sidebar-menu {{ list-style: none; }}
        .sidebar-menu li {{ margin-bottom: 2px; }}
        .sidebar-menu a {{ display: flex; align-items: center; gap: 12px; padding: 12px 25px; color: #bdc3c7; text-decoration: none; transition: all 0.3s; }}
        .sidebar-menu a:hover, .sidebar-menu a.active {{ background: #34495e; color: white; border-left: 3px solid #3498db; }}
        .sidebar-menu a i {{ width: 20px; text-align: center; }}
        .sidebar-section {{ padding: 15px 25px 5px; color: #7f8c8d; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }}
        
        /* Main content */
        .main {{ flex: 1; padding: 25px; overflow-y: auto; }}
        .page-title {{ font-size: 1.5rem; color: #2c3e50; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }}
        
        /* Cards grid */
        .card-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); cursor: pointer; transition: all 0.3s; border: 1px solid #eee; }}
        .card:hover {{ transform: translateY(-3px); box-shadow: 0 5px 20px rgba(0,0,0,0.12); border-color: #3498db; }}
        .card .icon {{ font-size: 2rem; margin-bottom: 10px; }}
        .card h3 {{ color: #2c3e50; font-size: 1rem; margin-bottom: 5px; }}
        .card p {{ color: #7f8c8d; font-size: 0.8rem; }}
        
        /* Tables */
        .table-container {{ background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 25px; }}
        .table-header {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }}
        .table-header h3 {{ font-size: 1rem; }}
        .btn-add {{ background: #27ae60; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.85rem; }}
        .btn-add:hover {{ background: #219a52; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 20px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
        th {{ background: #f8f9fa; color: #2c3e50; font-weight: 600; font-size: 0.85rem; }}
        tr:hover {{ background: #f8f9fa; }}
        .badge-success {{ background: #d4edda; color: #155724; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; }}
        .badge-warning {{ background: #fff3cd; color: #856404; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; }}
        .actions {{ display: flex; gap: 5px; }}
        .btn-action {{ border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 0.75rem; }}
        .btn-edit {{ background: #3498db; color: white; }}
        .btn-delete {{ background: #e74c3c; color: white; }}
        .btn-view {{ background: #95a5a6; color: white; }}
        
        /* Stats */
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 25px; }}
        .stat-card {{ background: white; border-radius: 10px; padding: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; align-items: center; gap: 20px; }}
        .stat-card .icon {{ width: 60px; height: 60px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }}
        .stat-card .info h4 {{ font-size: 1.8rem; color: #2c3e50; }}
        .stat-card .info p {{ color: #7f8c8d; font-size: 0.85rem; }}
        
        /* Forms */
        .form-container {{ background: white; border-radius: 10px; padding: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); max-width: 600px; }}
        .form-group {{ margin-bottom: 20px; }}
        .form-group label {{ display: block; margin-bottom: 5px; color: #2c3e50; font-weight: 500; }}
        .form-group input, .form-group select, .form-group textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 0.95rem; }}
        .form-group input:focus, .form-group select:focus {{ outline: none; border-color: #3498db; }}
        .btn-submit {{ background: #3498db; color: white; border: none; padding: 12px 25px; border-radius: 5px; cursor: pointer; font-size: 0.95rem; }}
        .btn-submit:hover {{ background: #2980b9; }}
        .btn-cancel {{ background: #95a5a6; color: white; border: none; padding: 12px 25px; border-radius: 5px; cursor: pointer; margin-left: 10px; }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .sidebar {{ display: none; }}
            .stats-grid {{ grid-template-columns: 1fr; }}
            .card-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-cash-register"></i> POS TPV</h1>
        <div class="user-info">
            <span><i class="fas fa-user-circle"></i> {nombre}</span>
            <span class="badge">{rol.upper()}</span>
            <button class="logout-btn" onclick="window.location.href='/logout'"><i class="fas fa-sign-out-alt"></i></button>
        </div>
    </div>
    <div class="status-bar">
        <span><i class="fas fa-circle" style="color: #2ecc71; font-size: 0.7rem;"></i> Terminal activa</span>
        <span id="hora"></span>
    </div>
    <div class="layout">
        <div class="sidebar">
            <ul class="sidebar-menu">
                <div class="sidebar-section">Principal</div>
                <li><a href="/" class="{'active' if title == 'Dashboard' else ''}"><i class="fas fa-home"></i> Dashboard</a></li>
                <li><a href="/ventas" class="{'active' if title == 'Ventas' else ''}"><i class="fas fa-shopping-cart"></i> Ventas</a></li>
                <li><a href="/productos" class="{'active' if title == 'Productos' else ''}"><i class="fas fa-box"></i> Productos</a></li>
                <li><a href="/clientes" class="{'active' if title == 'Clientes' else ''}"><i class="fas fa-users"></i> Clientes</a></li>
                
                <div class="sidebar-section">Gestión</div>
                <li><a href="/categorias" class="{'active' if title == 'Categorías' else ''}"><i class="fas fa-tags"></i> Categorías</a></li>
                <li><a href="/nomenclador" class="{'active' if title == 'Nomenclador' else ''}"><i class="fas fa-list"></i> Nomenclador</a></li>
                <li><a href="/usuarios" class="{'active' if title == 'Usuarios' else ''}"><i class="fas fa-user-cog"></i> Usuarios</a></li>
                <li><a href="/permisos" class="{'active' if title == 'Permisos' else ''}"><i class="fas fa-lock"></i> Permisos</a></li>
                
                <div class="sidebar-section">Reportes</div>
                <li><a href="/corte"><i class="fas fa-cash-register"></i> Corte de Caja</a></li>
                <li><a href="/estadisticas" class="{'active' if title == 'Estadísticas' else ''}"><i class="fas fa-chart-bar"></i> Estadísticas</a></li>
                <li><a href="/metricas" class="{'active' if title == 'Métricas' else ''}"><i class="fas fa-chart-line"></i> Métricas</a></li>
                
                <div class="sidebar-section">Sistema</div>
                <li><a href="/configuracion" class="{'active' if title == 'Configuración' else ''}"><i class="fas fa-cog"></i> Configuración</a></li>
                <li><a href="/seguridad" class="{'active' if title == 'Seguridad' else ''}"><i class="fas fa-shield-alt"></i> Seguridad</a></li>
                <li><a href="/auditoria" class="{'active' if title == 'Auditoría' else ''}"><i class="fas fa-clipboard-list"></i> Auditoría</a></li>
                <li><a href="/logs" class="{'active' if title == 'Logs' else ''}"><i class="fas fa-terminal"></i> Logs</a></li>
                <li><a href="/respaldo" class="{'active' if title == 'Respaldo' else ''}"><i class="fas fa-database"></i> Respaldo</a></li>
            </ul>
        </div>
        <div class="main">
            {content}
        </div>
    </div>
    <script>
        function actualizarHora() {{
            document.getElementById('hora').textContent = new Date().toLocaleString('es-ES');
        }}
        actualizarHora();
        setInterval(actualizarHora, 1000);
    </script>
</body>
</html>'''

def get_sidebar_item(title, icon, active=False):
    active_class = 'active' if active else ''
    return f'<li><a href="/{title.lower()}" class="{active_class}"><i class="fas {icon}"></i> {title}</a></li>'

# ========== CONTENIDO DE PÁGINAS ==========

def dashboard_content():
    # Estadísticas
    conn = get_conn()
    total_ventas = conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
    total_productos = conn.execute("SELECT COUNT(*) FROM productos WHERE activo = 1").fetchone()[0]
    total_clientes = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    total_usuarios = conn.execute("SELECT COUNT(*) FROM usuarios WHERE activo = 1").fetchone()[0]
    
    # Ventas del día
    hoy = datetime.now().strftime('%Y-%m-%d')
    ventas_dia = conn.execute("SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as monto FROM ventas WHERE DATE(fecha) = ?", (hoy,)).fetchone()
    
    # Productos con stock bajo
    stock_bajo = conn.execute("SELECT COUNT(*) FROM productos WHERE stock_actual <= stock_minimo AND activo = 1").fetchone()[0]
    
    conn.close()
    
    return f'''
    <h1 class="page-title"><i class="fas fa-home"></i> Dashboard</h1>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="icon" style="background: #e3f2fd; color: #1976d2;"><i class="fas fa-shopping-cart"></i></div>
            <div class="info">
                <h4>{total_ventas}</h4>
                <p>Ventas Totales</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="icon" style="background: #e8f5e9; color: #388e3c;"><i class="fas fa-box"></i></div>
            <div class="info">
                <h4>{total_productos}</h4>
                <p>Productos Activos</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="icon" style="background: #fff3e0; color: #f57c00;"><i class="fas fa-users"></i></div>
            <div class="info">
                <h4>{total_clientes}</h4>
                <p>Clientes</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="icon" style="background: #f3e5f5; color: #7b1fa2;"><i class="fas fa-user-tie"></i></div>
            <div class="info">
                <h4>{total_usuarios}</h4>
                <p>Usuarios Activos</p>
            </div>
        </div>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-calendar-day"></i> Ventas de Hoy</h3>
            </div>
            <div style="padding: 30px; text-align: center;">
                <div style="font-size: 3rem; color: #27ae60; margin-bottom: 10px;">${ventas_dia['monto']:,.2f}</div>
                <div style="color: #7f8c8d;">{ventas_dia['total']} ventas realizadas</div>
            </div>
        </div>
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-exclamation-triangle"></i> Alertas</h3>
            </div>
            <div style="padding: 20px;">
                <div style="padding: 15px; background: {'#ffebee' if stock_bajo > 0 else '#e8f5e9'}; border-radius: 5px; color: {'#c62828' if stock_bajo > 0 else '#2e7d32'};">
                    <i class="fas {'fa-exclamation-circle' if stock_bajo > 0 else 'fa-check-circle'}"></i>
                    {stock_bajo} productos con stock bajo
                </div>
            </div>
        </div>
    </div>
    
    <div class="card-grid" style="margin-top: 25px;">
        <div class="card" onclick="window.location.href='/ventas/nueva'">
            <div class="icon" style="color: #3498db;"><i class="fas fa-plus-circle"></i></div>
            <h3>Nueva Venta</h3>
            <p>Iniciar transacción</p>
        </div>
        <div class="card" onclick="window.location.href='/productos'">
            <div class="icon" style="color: #e67e22;"><i class="fas fa-boxes"></i></div>
            <h3>Inventario</h3>
            <p>Ver productos</p>
        </div>
        <div class="card" onclick="window.location.href='/corte'">
            <div class="icon" style="color: #f39c12;"><i class="fas fa-calculator"></i></div>
            <h3>Corte de Caja</h3>
            <p>Reporte del día</p>
        </div>
        <div class="card" onclick="window.location.href='/estadisticas'">
            <div class="icon" style="color: #1abc9c;"><i class="fas fa-chart-pie"></i></div>
            <h3>Estadísticas</h3>
            <p>Análisis de ventas</p>
        </div>
    </div>
    '''

def productos_content():
    productos = buscar_tabla("productos p LEFT JOIN categorias c ON p.categoria = c.id", 
                              "p.*, c.nombre as categoria_nombre", "p.activo = 1")
    
    rows = ''
    for p in productos:
        stock_class = 'badge-success' if p['stock_actual'] > p['stock_minimo'] else 'badge-warning'
        rows += f'''
        <tr>
            <td>{p['codigo']}</td>
            <td>{p['nombre']}</td>
            <td>{p['categoria_nombre'] or 'Sin categoría'}</td>
            <td>${p['precio']:.2f}</td>
            <td><span class="{stock_class}">{p['stock_actual']}</span></td>
            <td class="actions">
                <button class="btn-action btn-edit"><i class="fas fa-edit"></i></button>
                <button class="btn-action btn-delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>'''
    
    return f'''
    <h1 class="page-title"><i class="fas fa-box"></i> Gestión de Productos</h1>
    
    <div class="card-grid">
        <div class="card" onclick="window.location.href='/productos/nuevo'">
            <div class="icon" style="color: #27ae60;"><i class="fas fa-plus"></i></div>
            <h3>Nuevo Producto</h3>
            <p>Agregar al catálogo</p>
        </div>
        <div class="card" onclick="window.location.href='/categorias'">
            <div class="icon" style="color: #9b59b6;"><i class="fas fa-tags"></i></div>
            <h3>Categorías</h3>
            <p>Gestionar categorías</p>
        </div>
        <div class="card" onclick="window.location.href='/inventario'">
            <div class="icon" style="color: #3498db;"><i class="fas fa-warehouse"></i></div>
            <h3>Inventario</h3>
            <p>Ajustar stock</p>
        </div>
    </div>
    
    <div class="table-container">
        <div class="table-header">
            <h3><i class="fas fa-list"></i> Catálogo de Productos ({len(productos)})</h3>
            <button class="btn-add"><i class="fas fa-plus"></i> Nuevo</button>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Código</th>
                    <th>Nombre</th>
                    <th>Categoría</th>
                    <th>Precio</th>
                    <th>Stock</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    '''

def categorias_content():
    categorias = buscar_tabla("categorias")
    
    rows = ''
    for c in categorias:
        rows += f'''
        <tr>
            <td>{c['id']}</td>
            <td>{c['nombre']}</td>
            <td>{c['descripcion'] or '-'}</td>
            <td><span class="badge-success">Activo</span></td>
            <td class="actions">
                <button class="btn-action btn-edit"><i class="fas fa-edit"></i></button>
                <button class="btn-action btn-delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>'''
    
    return f'''
    <h1 class="page-title"><i class="fas fa-tags"></i> Gestión de Categorías</h1>
    
    <div class="table-container">
        <div class="table-header">
            <h3><i class="fas fa-list"></i> Categorías ({len(categorias)})</h3>
            <button class="btn-add"><i class="fas fa-plus"></i> Nueva</button>
        </div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nombre</th>
                    <th>Descripción</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    '''

def clientes_content():
    clientes = buscar_tabla("clientes")
    
    rows = ''
    for c in clientes:
        rows += f'''
        <tr>
            <td>{c['id']}</td>
            <td>{c['nombre']}</td>
            <td>{c['email'] or '-'}</td>
            <td>{c['telefono'] or '-'}</td>
            <td>{c['direccion'] or '-'}</td>
            <td class="actions">
                <button class="btn-action btn-view"><i class="fas fa-eye"></i></button>
                <button class="btn-action btn-edit"><i class="fas fa-edit"></i></button>
                <button class="btn-action btn-delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>'''
    
    return f'''
    <h1 class="page-title"><i class="fas fa-users"></i> Gestión de Clientes</h1>
    
    <div class="card-grid">
        <div class="card" onclick="window.location.href='/clientes/nuevo'">
            <div class="icon" style="color: #27ae60;"><i class="fas fa-user-plus"></i></div>
            <h3>Nuevo Cliente</h3>
            <p>Registrar cliente</p>
        </div>
        <div class="card">
            <div class="icon" style="color: #3498db;"><i class="fas fa-search"></i></div>
            <h3>Buscar</h3>
            <p>Buscar cliente</p>
        </div>
    </div>
    
    <div class="table-container">
        <div class="table-header">
            <h3><i class="fas fa-list"></i> Lista de Clientes ({len(clientes)})</h3>
            <button class="btn-add"><i class="fas fa-plus"></i> Nuevo</button>
        </div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nombre</th>
                    <th>Email</th>
                    <th>Teléfono</th>
                    <th>Dirección</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    '''

def usuarios_content():
    usuarios = buscar_tabla("usuarios")
    
    rows = ''
    for u in usuarios:
        rol_colors = {'admin': 'badge-danger', 'desarrollador': 'badge-warning', 'vendedor': 'badge-success', 'cajero': 'badge-success'}
        rows += f'''
        <tr>
            <td>{u['id']}</td>
            <td>{u['username']}</td>
            <td>{u['nombre']}</td>
            <td><span class="{rol_colors.get(u['rol'], 'badge-success')}">{u['rol'].upper()}</span></td>
            <td>{'Activo' if u['activo'] else 'Inactivo'}</td>
            <td class="actions">
                <button class="btn-action btn-edit"><i class="fas fa-edit"></i></button>
                <button class="btn-action btn-delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>'''
    
    return f'''
    <h1 class="page-title"><i class="fas fa-user-cog"></i> Gestión de Usuarios</h1>
    
    <div class="card-grid">
        <div class="card" onclick="window.location.href='/usuarios/nuevo'">
            <div class="icon" style="color: #27ae60;"><i class="fas fa-user-plus"></i></div>
            <h3>Nuevo Usuario</h3>
            <p>Crear cuenta</p>
        </div>
        <div class="card" onclick="window.location.href='/permisos'">
            <div class="icon" style="color: #e74c3c;"><i class="fas fa-lock"></i></div>
            <h3>Permisos</h3>
            <p>Gestionar permisos</p>
        </div>
    </div>
    
    <div class="table-container">
        <div class="table-header">
            <h3><i class="fas fa-list"></i> Usuarios ({len(usuarios)})</h3>
            <button class="btn-add"><i class="fas fa-plus"></i> Nuevo</button>
        </div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>Nombre</th>
                    <th>Rol</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    '''

def permisos_content():
    permisos = buscar_tabla("permisos")
    
    rows = ''
    for p in permisos:
        rows += f'''
        <tr>
            <td>{p['rol']}</td>
            <td>{p['modulo']}</td>
            <td>{'✅' if p['puede_ver'] else '❌'}</td>
            <td>{'✅' if p['puede_crear'] else '❌'}</td>
            <td>{'✅' if p['puede_editar'] else '❌'}</td>
            <td>{'✅' if p['puede_eliminar'] else '❌'}</td>
            <td class="actions">
                <button class="btn-action btn-edit"><i class="fas fa-edit"></i></button>
            </td>
        </tr>'''
    
    return f'''
    <h1 class="page-title"><i class="fas fa-lock"></i> Gestión de Permisos</h1>
    
    <div class="table-container">
        <div class="table-header">
            <h3><i class="fas fa-list"></i> Permisos por Rol</h3>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Rol</th>
                    <th>Módulo</th>
                    <th>Ver</th>
                    <th>Crear</th>
                    <th>Editar</th>
                    <th>Eliminar</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>{rows if rows else '<tr><td colspan="7" style="text-align:center;">Sin permisos configurados</td></tr>'}</tbody>
        </table>
    </div>
    '''

def nomenclador_content():
    nomencladores = buscar_tabla("nomenclador")
    
    rows = ''
    for n in nomencladores:
        rows += f'''
        <tr>
            <td>{n['tipo']}</td>
            <td>{n['codigo']}</td>
            <td>{n['descripcion']}</td>
            <td><span class="badge-success">Activo</span></td>
            <td class="actions">
                <button class="btn-action btn-edit"><i class="fas fa-edit"></i></button>
                <button class="btn-action btn-delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>'''
    
    return f'''
    <h1 class="page-title"><i class="fas fa-list"></i> Nomenclador</h1>
    
    <p style="color: #7f8c8d; margin-bottom: 20px;">Catálogos de códigos y clasificaciones del sistema</p>
    
    <div class="table-container">
        <div class="table-header">
            <h3><i class="fas fa-list"></i> Registros ({len(nomencladores)})</h3>
            <button class="btn-add"><i class="fas fa-plus"></i> Nuevo</button>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Tipo</th>
                    <th>Código</th>
                    <th>Descripción</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    '''

def estadisticas_content():
    conn = get_conn()
    
    # Ventas por día (últimos 7 días)
    ventas_dia = conn.execute("""
        SELECT DATE(fecha) as dia, COUNT(*) as total, SUM(total) as monto 
        FROM ventas GROUP BY DATE(fecha) ORDER BY dia DESC LIMIT 7
    """).fetchall()
    
    # Productos más vendidos
    top_productos = conn.execute("""
        SELECT p.nombre, SUM(dv.cantidad) as vendidos
        FROM detalle_ventas dv
        JOIN productos p ON dv.producto_id = p.id
        GROUP BY p.id ORDER BY vendidos DESC LIMIT 5
    """).fetchall()
    
    # Ventas por método de pago
    metodos_pago = conn.execute("""
        SELECT metodo_pago, COUNT(*) as total, SUM(total) as monto
        FROM ventas GROUP BY metodo_pago
    """).fetchall()
    
    conn.close()
    
    rows_ventas = ''
    for v in ventas_dia:
        rows_ventas += f'<tr><td>{v["dia"]}</td><td>{v["total"]}</td><td>${v["monto"]:,.2f}</td></tr>'
    
    rows_top = ''
    for i, p in enumerate(top_productos, 1):
        rows_top += f'<tr><td>{i}</td><td>{p["nombre"]}</td><td>{p["vendidos"]}</td></tr>'
    
    rows_metodos = ''
    for m in metodos_pago:
        rows_metodos += f'<tr><td>{m["metodo_pago"]}</td><td>{m["total"]}</td><td>${m["monto"]:,.2f}</td></tr>'
    
    return f'''
    <h1 class="page-title"><i class="fas fa-chart-bar"></i> Estadísticas</h1>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-calendar"></i> Ventas por Día</h3>
            </div>
            <table>
                <thead><tr><th>Fecha</th><th>Ventas</th><th>Monto</th></tr></thead>
                <tbody>{rows_ventas if rows_ventas else '<tr><td colspan="3" style="text-align:center;">Sin datos</td></tr>'}</tbody>
            </table>
        </div>
        
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-trophy"></i> Productos Más Vendidos</h3>
            </div>
            <table>
                <thead><tr><th>#</th><th>Producto</th><th>Unidades</th></tr></thead>
                <tbody>{rows_top if rows_top else '<tr><td colspan="3" style="text-align:center;">Sin datos</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    
    <div class="table-container" style="margin-top: 20px;">
        <div class="table-header">
            <h3><i class="fas fa-credit-card"></i> Ventas por Método de Pago</h3>
        </div>
        <table>
            <thead><tr><th>Método</th><th>Cantidad</th><th>Total</th></tr></thead>
            <tbody>{rows_metodos if rows_metodos else '<tr><td colspan="3" style="text-align:center;">Sin datos</td></tr>'}</tbody>
        </table>
    </div>
    '''

def seguridad_content():
    conn = get_conn()
    
    # Intentos de login recientes
    intentos = conn.execute("SELECT * FROM intentos_login ORDER BY fecha DESC LIMIT 20").fetchall()
    
    # Sesiones activas
    sesiones = conn.execute("""
        s.*, u.nombre, u.username 
        FROM sesiones s 
        LEFT JOIN usuarios u ON s.usuario_id = u.id 
        WHERE s.activa = 1
    """).fetchall()
    
    conn.close()
    
    rows_intentos = ''
    for i in intentos:
        color = '#27ae60' if i['exito'] else '#e74c3c'
        rows_intentos += f'<tr><td>{i["username"]}</td><td>{str(i["ip"] or "-")}</td><td style="color: {color}">{"✅ Éxito" if i["exito"] else "❌ Fallido"}</td><td>{i["fecha"]}</td></tr>'
    
    rows_sesiones = ''
    for s in sesiones:
        rows_sesiones += f'<tr><td>{s["username"]}</td><td>{s["ip"] or "-"}</td><td>{s["creada_en"]}</td><td><span class="badge-success">Activa</span></td></tr>'
    
    return f'''
    <h1 class="page-title"><i class="fas fa-shield-alt"></i> Seguridad</h1>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="icon" style="background: #e3f2fd; color: #1976d2;"><i class="fas fa-sign-in-alt"></i></div>
            <div class="info">
                <h4>{len(intentos)}</h4>
                <p>Intentos de Login</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="icon" style="background: #e8f5e9; color: #388e3c;"><i class="fas fa-user-check"></i></div>
            <div class="info">
                <h4>{len(sesiones)}</h4>
                <p>Sesiones Activas</p>
            </div>
        </div>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-history"></i> Intentos de Login</h3>
            </div>
            <table>
                <thead><tr><th>Usuario</th><th>IP</th><th>Estado</th><th>Fecha</th></tr></thead>
                <tbody>{rows_intentos if rows_intentos else '<tr><td colspan="4" style="text-align:center;">Sin registros</td></tr>'}</tbody>
            </table>
        </div>
        
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-users"></i> Sesiones Activas</h3>
            </div>
            <table>
                <thead><tr><th>Usuario</th><th>IP</th><th>Inicio</th><th>Estado</th></tr></thead>
                <tbody>{rows_sesiones if rows_sesiones else '<tr><td colspan="4" style="text-align:center;">Sin sesiones</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    '''

def auditoria_content():
    auditoria = buscar_tabla("auditoria", limite=50)
    
    rows = ''
    for a in auditoria:
        rows += f'''
        <tr>
            <td>{a['id']}</td>
            <td>{a['usuario_id'] or 'Sistema'}</td>
            <td>{a['accion']}</td>
            <td>{a['tabla'] or '-'}</td>
            <td>{a['fecha']}</td>
            <td class="actions">
                <button class="btn-action btn-view"><i class="fas fa-eye"></i></button>
            </td>
        </tr>'''
    
    return f'''
    <h1 class="page-title"><i class="fas fa-clipboard-list"></i> Auditoría</h1>
    
    <p style="color: #7f8c8d; margin-bottom: 20px;">Registro de todas las acciones realizadas en el sistema</p>
    
    <div class="table-container">
        <div class="table-header">
            <h3><i class="fas fa-list"></i> Registro de Auditoría</h3>
        </div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Usuario</th>
                    <th>Acción</th>
                    <th>Tabla</th>
                    <th>Fecha</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>{rows if rows else '<tr><td colspan="6" style="text-align:center;">Sin registros</td></tr>'}</tbody>
        </table>
    </div>
    '''

def logs_content():
    logs = buscar_tabla("logs", limite=50)
    
    rows = ''
    for log in logs:
        color = '#27ae60' if log['nivel'] == 'INFO' else '#f39c12' if log['nivel'] == 'WARNING' else '#e74c3c'
        rows += f'''
        <tr>
            <td>{log['id']}</td>
            <td style="color: {color}">{log['nivel']}</td>
            <td>{log['modulo']}</td>
            <td>{log['mensaje']}</td>
            <td>{log['creado_en']}</td>
        </tr>'''
    
    return f'''
    <h1 class="page-title"><i class="fas fa-terminal"></i> Logs del Sistema</h1>
    
    <div class="table-container">
        <div class="table-header">
            <h3><i class="fas fa-list"></i> Registro de Logs</h3>
        </div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nivel</th>
                    <th>Módulo</th>
                    <th>Mensaje</th>
                    <th>Fecha</th>
                </tr>
            </thead>
            <tbody>{rows if rows else '<tr><td colspan="5" style="text-align:center;">Sin logs</td></tr>'}</tbody>
        </table>
    </div>
    '''

def configuracion_content():
    config = buscar_tabla("configuracion")
    
    rows = ''
    for c in config:
        rows += f'''
        <tr>
            <td>{c['clave']}</td>
            <td>{c['valor']}</td>
            <td>{c['descripcion']}</td>
            <td class="actions">
                <button class="btn-action btn-edit"><i class="fas fa-edit"></i></button>
            </td>
        </tr>'''
    
    return f'''
    <h1 class="page-title"><i class="fas fa-cog"></i> Configuración</h1>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-store"></i> Datos del Negocio</h3>
            </div>
            <table>
                <thead><tr><th>Clave</th><th>Valor</th><th>Descripción</th><th>Acciones</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-sliders-h"></i> Opciones del Sistema</h3>
            </div>
            <div style="padding: 20px;">
                <div style="padding: 15px; background: #f8f9fa; border-radius: 5px; margin-bottom: 10px; cursor: pointer;">
                    <i class="fas fa-users"></i> Gestión de Usuarios
                </div>
                <div style="padding: 15px; background: #f8f9fa; border-radius: 5px; margin-bottom: 10px; cursor: pointer;">
                    <i class="fas fa-shield-alt"></i> Seguridad
                </div>
                <div style="padding: 15px; background: #f8f9fa; border-radius: 5px; margin-bottom: 10px; cursor: pointer;">
                    <i class="fas fa-database"></i> Base de Datos
                </div>
                <div style="padding: 15px; background: #f8f9fa; border-radius: 5px; cursor: pointer;">
                    <i class="fas fa-print"></i> Impresora
                </div>
            </div>
        </div>
    </div>
    '''

def corte_content():
    hoy = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_conn()
    resultado = conn.execute("SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as suma FROM ventas WHERE DATE(fecha) = ?", (hoy,)).fetchone()
    metodos = conn.execute("SELECT metodo_pago, COUNT(*) as count, SUM(total) as total FROM ventas WHERE DATE(fecha) = ? GROUP BY metodo_pago", (hoy,)).fetchall()
    
    # Ventas del día
    ventas_dia = conn.execute("SELECT * FROM ventas WHERE DATE(fecha) = ? ORDER BY fecha DESC", (hoy,)).fetchall()
    conn.close()
    
    rows_metodos = ''
    for m in metodos:
        rows_metodos += f'<tr><td>{m["metodo_pago"]}</td><td>{m["count"]}</td><td>${m["total"]:,.2f}</td></tr>'
    
    rows_ventas = ''
    for v in ventas_dia:
        rows_ventas += f'<tr><td>{v["id"]}</td><td>{v["fecha"]}</td><td>{v["metodo_pago"]}</td><td>${v["total"]:.2f}</td></tr>'
    
    return f'''
    <h1 class="page-title"><i class="fas fa-cash-register"></i> Corte de Caja</h1>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="icon" style="background: #e8f5e9; color: #388e3c;"><i class="fas fa-calendar-day"></i></div>
            <div class="info">
                <h4>{hoy}</h4>
                <p>Fecha del Corte</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="icon" style="background: #e3f2fd; color: #1976d2;"><i class="fas fa-shopping-cart"></i></div>
            <div class="info">
                <h4>{resultado['total']}</h4>
                <p>Ventas Realizadas</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="icon" style="background: #fff3e0; color: #f57c00;"><i class="fas fa-dollar-sign"></i></div>
            <div class="info">
                <h4>${resultado['suma']:,.2f}</h4>
                <p>Total del Día</p>
            </div>
        </div>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-credit-card"></i> Por Método de Pago</h3>
            </div>
            <table>
                <thead><tr><th>Método</th><th>Cantidad</th><th>Total</th></tr></thead>
                <tbody>{rows_metodos if rows_metodos else '<tr><td colspan="3" style="text-align:center;">Sin ventas</td></tr>'}</tbody>
            </table>
        </div>
        
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-receipt"></i> Ventas del Día</h3>
            </div>
            <table>
                <thead><tr><th>#</th><th>Hora</th><th>Método</th><th>Total</th></tr></thead>
                <tbody>{rows_ventas if rows_ventas else '<tr><td colspan="4" style="text-align:center;">Sin ventas</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    '''

def ventas_content():
    return '''
    <h1 class="page-title"><i class="fas fa-shopping-cart"></i> Módulo de Ventas</h1>
    
    <div class="card-grid">
        <div class="card" onclick="window.location.href='/ventas/nueva'">
            <div class="icon" style="color: #27ae60;"><i class="fas fa-plus-circle"></i></div>
            <h3>Nueva Venta</h3>
            <p>Iniciar venta rápida</p>
        </div>
        <div class="card">
            <div class="icon" style="color: #3498db;"><i class="fas fa-list"></i></div>
            <h3>Historial</h3>
            <p>Ver ventas anteriores</p>
        </div>
        <div class="card">
            <div class="icon" style="color: #e74c3c;"><i class="fas fa-undo"></i></div>
            <h3>Devoluciones</h3>
            <p>Procesar devolución</p>
        </div>
        <div class="card">
            <div class="icon" style="color: #f39c12;"><i class="fas fa-file-invoice"></i></div>
            <h3>Facturación</h3>
            <p>Generar factura</p>
        </div>
    </div>
    '''

def metricas_content():
    conn = get_conn()
    
    # Métricas generales
    total_ventas = conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
    total_productos = conn.execute("SELECT COUNT(*) FROM productos WHERE activo = 1").fetchone()[0]
    total_clientes = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    
    # Promedio de venta
    promedio = conn.execute("SELECT COALESCE(AVG(total), 0) FROM ventas").fetchone()[0]
    
    # Ventas por vendedor
    por_vendedor = conn.execute("""
        SELECT vendedor, COUNT(*) as total, SUM(total) as monto 
        FROM ventas GROUP BY vendedor ORDER BY monto DESC
    """).fetchall()
    
    # Productos sin stock
    sin_stock = conn.execute("SELECT COUNT(*) FROM productos WHERE stock_actual = 0 AND activo = 1").fetchone()[0]
    
    conn.close()
    
    rows_vendedores = ''
    for v in por_vendedor:
        rows_vendedores += f'<tr><td>{v["vendedor"] or "Sin asignar"}</td><td>{v["total"]}</td><td>${v["monto"] or 0:,.2f}</td></tr>'
    
    return f'''
    <h1 class="page-title"><i class="fas fa-chart-line"></i> Métricas</h1>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="icon" style="background: #e3f2fd; color: #1976d2;"><i class="fas fa-shopping-bag"></i></div>
            <div class="info">
                <h4>{total_ventas}</h4>
                <p>Total Ventas</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="icon" style="background: #e8f5e9; color: #388e3c;"><i class="fas fa-calculator"></i></div>
            <div class="info">
                <h4>${promedio:,.2f}</h4>
                <p>Promedio por Venta</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="icon" style="background: #fff3e0; color: #f57c00;"><i class="fas fa-box"></i></div>
            <div class="info">
                <h4>{total_productos}</h4>
                <p>Productos Activos</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="icon" style="background: #ffebee; color: #c62828;"><i class="fas fa-exclamation-triangle"></i></div>
            <div class="info">
                <h4>{sin_stock}</h4>
                <p>Sin Stock</p>
            </div>
        </div>
    </div>
    
    <div class="table-container" style="margin-top: 20px;">
        <div class="table-header">
            <h3><i class="fas fa-user-tie"></i> Rendimiento por Vendedor</h3>
        </div>
        <table>
            <thead><tr><th>Vendedor</th><th>Ventas</th><th>Monto Total</th></tr></thead>
            <tbody>{rows_vendedores if rows_vendedores else '<tr><td colspan="3" style="text-align:center;">Sin datos</td></tr>'}</tbody>
        </table>
    </div>
    '''

def respaldo_content():
    return '''
    <h1 class="page-title"><i class="fas fa-database"></i> Respaldo y Restauración</h1>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-download"></i> Crear Respaldo</h3>
            </div>
            <div style="padding: 25px;">
                <p style="color: #7f8c8d; margin-bottom: 20px;">Genera una copia de seguridad de la base de datos</p>
                <button class="btn-add" style="width: 100%; padding: 15px;">
                    <i class="fas fa-file-download"></i> Generar Respaldo
                </button>
            </div>
        </div>
        
        <div class="table-container">
            <div class="table-header">
                <h3><i class="fas fa-upload"></i> Restaurar</h3>
            </div>
            <div style="padding: 25px;">
                <p style="color: #7f8c8d; margin-bottom: 20px;">Restaurar desde un archivo de respaldo</p>
                <input type="file" style="margin-bottom: 15px;">
                <button class="btn-add" style="width: 100%; padding: 15px; background: #3498db;">
                    <i class="fas fa-file-upload"></i> Restaurar
                </button>
            </div>
        </div>
    </div>
    '''

# ========== HANDLER HTTP ==========

class POSHandler(http.server.BaseHTTPRequestHandler):
    usuario_default = {'nombre': 'Desarrollador', 'rol': 'desarrollador'}
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        # Páginas
        pages = {
            '/': ('Dashboard', dashboard_content),
            '/login': ('Login', lambda: '<h1>Login</h1>'),
            '/ventas': ('Ventas', ventas_content),
            '/productos': ('Productos', productos_content),
            '/categorias': ('Categorías', categorias_content),
            '/clientes': ('Clientes', clientes_content),
            '/usuarios': ('Usuarios', usuarios_content),
            '/permisos': ('Permisos', permisos_content),
            '/nomenclador': ('Nomenclador', nomenclador_content),
            '/estadisticas': ('Estadísticas', estadisticas_content),
            '/metricas': ('Métricas', metricas_content),
            '/seguridad': ('Seguridad', seguridad_content),
            '/auditoria': ('Auditoría', auditoria_content),
            '/logs': ('Logs', logs_content),
            '/configuracion': ('Configuración', configuracion_content),
            '/corte': ('Corte de Caja', corte_content),
            '/respaldo': ('Respaldo', respaldo_content),
        }
        
        if path in pages:
            title, content_func = pages[path]
            html = get_html(title, content_func(), self.usuario_default)
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode())
        elif path == '/logout':
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Silenciar logs en consola

# ========== INICIAR SERVIDOR ==========

if __name__ == '__main__':
    PORT = 8080
    server = http.server.HTTPServer(('0.0.0.0', PORT), POSHandler)
    print(f'🚀 Servidor POS TPV iniciado')
    print(f'📱 Abre en tu navegador: http://localhost:{PORT}')
    print(f'🛑 Presiona Ctrl+C para detener')
    server.serve_forever()
