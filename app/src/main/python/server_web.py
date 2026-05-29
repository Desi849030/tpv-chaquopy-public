import http.server
import json
import sqlite3
import os
from urllib.parse import urlparse, parse_qs

DB_FILE = 'data/tpv.db'

class POSHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/':
            self.send_html(self.get_index_html())
        elif parsed.path == '/api/productos':
            self.send_json(self.get_productos())
        elif parsed.path == '/api/clientes':
            self.send_json(self.get_clientes())
        elif parsed.path == '/api/ventas':
            self.send_json(self.get_ventas())
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_productos(self):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos WHERE activo = 1")
        productos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return productos
    
    def get_clientes(self):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes")
        clientes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return clientes
    
    def get_ventas(self):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC LIMIT 50")
        ventas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ventas
    
    def get_index_html(self):
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>POS TPV - Sistema de Punto de Venta</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 1.5rem; }
        .header .user-info { display: flex; align-items: center; gap: 10px; }
        .container { max-width: 1200px; margin: 20px auto; padding: 0 20px; }
        .menu-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 5px 20px rgba(0,0,0,0.15); }
        .card .icon { font-size: 2.5rem; margin-bottom: 10px; }
        .card h3 { color: #2c3e50; margin-bottom: 5px; }
        .card p { color: #7f8c8d; font-size: 0.9rem; }
        .status-bar { background: #27ae60; color: white; padding: 10px 20px; text-align: center; }
        .logout-btn { background: #e74c3c; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-cash-register"></i> POS TPV</h1>
        <div class="user-info">
            <span><i class="fas fa-user"></i> Desarrollador</span>
            <button class="logout-btn" onclick="alert('Sesión cerrada')"><i class="fas fa-sign-out-alt"></i></button>
        </div>
    </div>
    <div class="status-bar">
        <i class="fas fa-circle" style="color: #2ecc71;"></i> Terminal activa - <span id="hora"></span>
    </div>
    <div class="container">
        <div class="menu-grid">
            <div class="card" onclick="cargarSeccion('ventas')">
                <div class="icon" style="color: #3498db;"><i class="fas fa-shopping-cart"></i></div>
                <h3>Nueva Venta</h3>
                <p>Registrar venta a cliente</p>
            </div>
            <div class="card" onclick="cargarSeccion('productos')">
                <div class="icon" style="color: #e67e22;"><i class="fas fa-box"></i></div>
                <h3>Productos</h3>
                <p>Catálogo y stock</p>
            </div>
            <div class="card" onclick="cargarSeccion('clientes')">
                <div class="icon" style="color: #9b59b6;"><i class="fas fa-users"></i></div>
                <h3>Clientes</h3>
                <p>Gestionar clientes</p>
            </div>
            <div class="card" onclick="cargarSeccion('corte')">
                <div class="icon" style="color: #f39c12;"><i class="fas fa-cash-register"></i></div>
                <h3>Corte de Caja</h3>
                <p>Reporte del día</p>
            </div>
            <div class="card" onclick="cargarSeccion('estadisticas')">
                <div class="icon" style="color: #1abc9c;"><i class="fas fa-chart-bar"></i></div>
                <h3>Estadísticas</h3>
                <p>Ventas y más vendidos</p>
            </div>
            <div class="card" onclick="cargarSeccion('configuracion')">
                <div class="icon" style="color: #95a5a6;"><i class="fas fa-cog"></i></div>
                <h3>Configuración</h3>
                <p>Ajustes del sistema</p>
            </div>
        </div>
        <div id="contenido" style="margin-top: 30px;"></div>
    </div>
    <script>
        document.getElementById('hora').textContent = new Date().toLocaleString();
        function cargarSeccion(seccion) {
            const contenido = document.getElementById('contenido');
            if(seccion === 'productos') {
                fetch('/api/productos').then(r => r.json()).then(data => {
                    let html = '<h2><i class="fas fa-box"></i> Productos</h2><table style="width:100%;border-collapse:collapse;"><tr style="background:#2c3e50;color:white;"><th>Código</th><th>Nombre</th><th>Precio</th><th>Stock</th></tr>';
                    data.forEach(p => {
                        html += `<tr style="border-bottom:1px solid #ddd;"><td>${p.codigo}</td><td>${p.nombre}</td><td>$${p.precio}</td><td>${p.stock_actual}</td></tr>`;
                    });
                    html += '</table>';
                    contenido.innerHTML = html;
                });
            } else if(seccion === 'clientes') {
                fetch('/api/clientes').then(r => r.json()).then(data => {
                    let html = '<h2><i class="fas fa-users"></i> Clientes</h2><table style="width:100%;border-collapse:collapse;"><tr style="background:#2c3e50;color:white;"><th>Nombre</th><th>Email</th><th>Teléfono</th></tr>';
                    data.forEach(c => {
                        html += `<tr style="border-bottom:1px solid #ddd;"><td>${c.nombre}</td><td>${c.email || 'N/A'}</td><td>${c.telefono || 'N/A'}</td></tr>`;
                    });
                    html += '</table>';
                    contenido.innerHTML = html;
                });
            } else {
                contenido.innerHTML = `<h2>Sección: ${seccion}</h2><p>En desarrollo...</p>`;
            }
        }
    </script>
</body>
</html>'''

if __name__ == '__main__':
    PORT = 8080
    server = http.server.HTTPServer(('0.0.0.0', PORT), POSHandler)
    print(f'Servidor web POS iniciado en http://localhost:{PORT}')
    server.serve_forever()
