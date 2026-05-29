/**
 * TPV Ultra Smart - Boot/Inicio de la aplicacion
 */

async function verificarServidor() {
    try {
        const res = await fetch("/api/health", { 
            signal: AbortSignal.timeout(5000)
        });
        const data = await res.json();
        console.log("Servidor conectado: v" + data.version);
        return true;
    } catch (e) {
        console.warn("Servidor no disponible:", e.message);
        return false;
    }
}

async function boot() {
    console.log("TPV Ultra Smart - Iniciando...");
    
    const servidorActivo = await verificarServidor();
    
    if (!servidorActivo) {
        console.warn("Iniciando en modo offline...");
    }
    
    if (TPV_AUTH.haySesion()) {
        const sesion = TPV_AUTH.obtenerSesion();
        console.log("Sesion activa: " + sesion.usuario + " (" + sesion.rol + ")");
        TPV_AGENT.saludoPorRol(sesion.rol, sesion.nombre);
        mostrarApp();
        const rutas = {
            desarrollador: "#/dashboard",
            administrador: "#/dashboard",
            empleado: "#/tienda",
            cliente: "#/catalogo"
        };
        window.location.hash = rutas[sesion.rol] || "#/catalogo";
    } else {
        TPV_AGENT.saludoInvitado();
        setTimeout(function() {
            const splash = document.getElementById("splash");
            const login = document.getElementById("login");
            if (splash) splash.style.display = "none";
            if (login) login.style.display = "block";
        }, 1500);
    }
    
    console.log("TPV Ultra Smart listo");
}

function mostrarApp() {
    const loginDiv = document.getElementById("login");
    const appDiv = document.getElementById("app");
    const splash = document.getElementById("splash");
    if (splash) splash.style.display = "none";
    if (loginDiv) loginDiv.style.display = "none";
    if (appDiv) appDiv.style.display = "block";
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
} else {
    boot();
}
