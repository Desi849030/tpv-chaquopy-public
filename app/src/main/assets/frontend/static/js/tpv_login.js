async function login() {
    const user = document.getElementById("user").value.trim();
    const pass = document.getElementById("pass").value.trim();
    const errBox = document.getElementById("err");
    const errMsg = document.getElementById("errmsg");

    errBox.style.display = "none";

    const data = await TPV_AUTH.cargarUsuarios();
    if (!data) {
        errMsg.textContent = "Error cargando configuración.";
        errBox.style.display = "flex";
        return;
    }

    if (user === data.desarrollador.usuario && pass === data.desarrollador.password) {
        TPV_AUTH.guardarSesion(user, "desarrollador");
        mostrarApp();
        TPV_AGENT.saludoPorRol("desarrollador", user);
        window.location.hash = "#/dashboard";
        return;
    }

    const admin = data.administradores.find(a => a.usuario === user && a.password === pass);
    if (admin) {
        TPV_AUTH.guardarSesion(user, "administrador");
        mostrarApp();
        TPV_AGENT.saludoPorRol("administrador", user);
        window.location.hash = "#/dashboard";
        return;
    }

    const emp = data.empleados.find(e => e.usuario === user && e.password === pass);
    if (emp) {
        TPV_AUTH.guardarSesion(user, "empleado");
        mostrarApp();
        TPV_AGENT.saludoPorRol("empleado", user);
        window.location.hash = "#/tienda";
        return;
    }

    const cli = data.clientes.find(c => c.usuario === user && c.password === pass);
    if (cli) {
        TPV_AUTH.guardarSesion(user, "cliente");
        mostrarApp();
        TPV_AGENT.saludoPorRol("cliente", user);
        window.location.hash = "#/catalogo";
        return;
    }

    errMsg.textContent = "Usuario o contraseña incorrectos.";
    errBox.style.display = "flex";
}

function mostrarApp() {
    document.getElementById("login").style.display = "none";
    document.getElementById("app").style.display = "block";
}

document.addEventListener("click", e => {
    if (e.target.id === "btnLogin") login();
});
