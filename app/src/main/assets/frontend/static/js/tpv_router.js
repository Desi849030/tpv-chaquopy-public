async function cargarParcial(nombre) {
    const app = document.getElementById("app");
    const html = await fetch(`/templates/partials/${nombre}.html`).then(r => r.text());
    app.innerHTML = html;
}

function resolverRuta(hash) {
    if (!hash || hash === "#/" || hash === "") return "#/login";
    return hash;
}

async function proteger(vista) {
    const rol = TPV_AUTH.obtenerRol();
    if (!rol) {
        window.location.hash = "#/login";
        await cargarParcial("_login");
        return false;
    }
    if (!TPV_ROLES.puedeAcceder(rol, vista)) {
        window.location.hash = "#/login";
        await cargarParcial("_login");
        return false;
    }
    return true;
}

export function initRouter() {
    async function manejar() {
        const ruta = resolverRuta(window.location.hash);

        if (ruta === "#/login") {
            await cargarParcial("_login");
            TPV_AGENT.saludoInvitado();
            return;
        }

        if (ruta === "#/dashboard") {
            if (!(await proteger("dashboard"))) return;
            await cargarParcial("_dashboard");
            return;
        }

        if (ruta === "#/catalogo") {
            if (!(await proteger("catalogo"))) return;
            await cargarParcial("_catalogo");
            return;
        }

        if (ruta === "#/tienda") {
            if (!(await proteger("tienda"))) return;
            await cargarParcial("_tienda");
            return;
        }

        window.location.hash = "#/login";
        await cargarParcial("_login");
        TPV_AGENT.saludoInvitado();
    }

    window.addEventListener("hashchange", manejar);
    manejar();
}

