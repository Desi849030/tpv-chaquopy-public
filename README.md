# 🏪 TPV Ultra Smart v8.9

Sistema de Punto de Venta (TPV) profesional con IA integrada, multi-rol, sincronización con la nube y diagnóstico de telecomunicaciones real.

## 🌟 Características principales

### 🛒 Operación
- **Punto de Venta** con vista de catálogo y orden actual
- **Tienda Online** con pedidos remotos
- **Etiquetas QR** para productos
- **Multi-tienda** con sincronización

### 📦 Catálogo
- Gestión de productos con imágenes (emojis o URLs)
- Categorías personalizables
- Stock e inventario con alertas de mínimo
- Importar/exportar Excel

### 💰 Ventas
- Ventas del día en tiempo real
- Nomenclador de caja para arqueos
- Historial completo y cierres
- Exportación a Excel

### 🤖 Asistente IA Universal
El chat IA funciona para **TODOS los roles** (incluso sin login):

| Rol | Capacidades |
|-----|-------------|
| **Cliente anónimo** | Catálogo, precios, ofertas, búsqueda, categorías, horarios |
| **Cliente logueado** | + pedidos personales, puntos |
| **Vendedor/Cajero** | + mis ventas, stock, productos top |
| **Supervisor** | + reportes, rotación, ABC, alertas |
| **Administrador** | + balance, gastos, vendedores, usuarios |
| **Desarrollador** | + telemetría, logs, **diagnóstico telecom REAL** |

### 📡 Diagnóstico Telecom (v8.2+)

El rol **desarrollador** dispone de herramientas REALES de red:
- Latencia y jitter a Supabase
- Throughput real de descarga
- DNS lookup con tiempo de resolución
- TLS handshake (versión, cipher, certificado)
- Información de red local (IP, hostname)
- IOPS de SQLite local

**Acceso:**
- Chat IA: `diagnóstico completo`, `mide la latencia`, `tls handshake`
- Menú: **Herramientas → Desarrollador → Diagnóstico Telecom**
- API: `/api/dev/telecom/*` (ver `docs/telecom_diagnostico.md`)

### 🔐 Seguridad
- Sesiones atómicas con `session_token` único por login
- Verificación de usuario activo en cada request (sin caché)
- RBAC (Role-Based Access Control) visual y backend
- RLS preparado para Supabase
- Headers de seguridad (CSP, X-Frame-Options, etc.)
- Rate limiting en login

### ☁️ Sincronización
- SQLite local (offline-first)
- Supabase para sync bidireccional opcional
- Soporta JWT clásicas y publishable keys
- Modo air-gapped funcional

## 🚀 Instalación rápida (Termux/Android)

```bash
# Clonar
git clone https://github.com/Desi849030/tpv-chaquopy.git
cd tpv-chaquopy

# Configurar Supabase (opcional)
cp .env.example .env
nano .env  # añadir SUPABASE_URL y SUPABASE_ANON_KEY

# Arrancar
bash tpv_termux_run.sh

# Abrir en navegador
# http://127.0.0.1:5050
