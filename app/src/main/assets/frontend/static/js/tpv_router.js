/**
 * TPV Ultra Smart - Router de la aplicacion
 */

const rutas = {
    "#/dashboard": { titulo: "Dashboard", roles: ["desarrollador", "administrador"] },
    "#/tienda": { titulo: "Tienda", roles: ["desarrollador", "administrador", "empleado"] },
    "#/inventario": { titulo: "Inventario", roles: ["desarrollador", "administrador"] },
    "#/productos": { titulo: "Productos", roles: ["desarrollador", "administrador", "empleado"] },
    "#/catalogo": { titulo: "Catalogo", roles: null }
};

export function initRouter() {
    console.log("Router iniciado");

    window.addEventListener("hashchange", manejarRuta);
    manejarRuta();
}

function manejarRuta() {
    const hash = window.location.hash || "#/catalogo";
    console.log("Navegando a: " + hash);

    const ruta = rutas[hash];
    const rol = TPV_AUTH.obtenerRol();

    if (ruta && ruta.roles && !ruta.roles.includes(rol)) {
        console.warn("Sin permisos para: " + hash);
        window.location.hash = "#/catalogo";
        return;
    }

    if (ruta && ruta.titulo) {
        document.title = ruta.titulo + " | TPV Ultra Smart";
    }

    renderizarContenido(hash, rol);
}

function renderizarContenido(hash, rol) {
    const app = document.getElementById("app");
    if (!app) return;

    const contenidos = {
        "#/dashboard": "<div class='dashboard-container'><h2>Dashboard</h2><p>Bienvenido al panel de control.</p><div id='stats'></div></div>",
        "#/tienda": "<div class='tienda-container'><h2>Tienda</h2><p>Gestiona las ventas y el catalogo.</p></div>",
        "#/catalogo": "<div class='catalogo-container'><h2>Catalogo</h2><p>Explora nuestros productos.</p><div id='productos-lista'></div></div>",
        "#/inventario": "<div class='inventario-container'><h2>Inventario</h2><p>Gestiona el stock de productos.</p></div>"
    };

    app.innerHTML = contenidos[hash] || contenidos["#/catalogo"];

    if (hash === "#/catalogo") {
        cargarProductos();
    }
    if (hash === "#/dashboard") {
        cargarDashboard();
    }
}

async function cargarProductos() {
    try {
        const res = await fetch("/api/productos");
        const data = await res.json();
        
        const lista = document.getElementById("productos-lista");
        if (!lista) return;
        
        if (!data.productos || data.productos.length === 0) {
            lista.innerHTML = "<p>No hay productos disponibles.</p>";
            return;
        }

        let html = "<div class='productos-grid'>";
        for (const p of data.productos) {
            html += "<div class='producto-item'>" +
                "<h4>" + p.nombre + "</h4>" +
                "<p class='precio'>$" + (p.precio || 0).toFixed(2) + "</p>" +
                "<p class='stock'>Stock: " + (p.stock_actual || "N/A") + "</p>" +
                "</div>";
        }
        html += "</div>";
        lista.innerHTML = html;
    } catch (e) {
        console.error("Error cargando productos:", e);
    }
}

async function cargarDashboard() {
    try {
        const res = await fetch("/api/agent/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: "stock", role: "administrador" })
        });
        const data = await res.json();
        
        const stats = document.getElementById("stats");
        if (stats) {
            stats.innerHTML = "<div class='card'>" + data.response + "</div>";
        }
    } catch (e) {
        console.error("Error cargando dashboard:", e);
    }
}
