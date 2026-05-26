async function validarLogin() {
    const u = document.getElementById("login_user").value;
    const p = document.getElementById("login_pass").value;
    const errorBox = document.getElementById("login_error");

    errorBox.style.display = "none";

    let data;
    try {
        data = await fetch("/config/users.json").then(r => r.json());
    } catch (e) {
        errorBox.textContent = "Error de configuración de usuarios.";
        errorBox.style.display = "block";
        return;
    }

    // Desarrollador
    if (u === data.desarrollador.usuario && p === data.desarrollador.password) {
        localStorage.setItem("rol", "desarrollador");
        window.location.hash = "#/dashboard";
        return;
    }

    // Administradores
    const admin = data.administradores.find(a => a.usuario === u && a.password === p);
    if (admin) {
        localStorage.setItem("rol", "administrador");
        window.location.hash = "#/dashboard";
        return;
    }

    // Empleados
    const emp = data.empleados.find(e => e.usuario === u && e.password === p);
    if (emp) {
        localStorage.setItem("rol", "empleado");
        window.location.hash = "#/tienda";
        return;
    }

    // Clientes
    const cli = data.clientes.find(c => c.usuario === u && c.password === p);
    if (cli) {
        localStorage.setItem("rol", "cliente");
        window.location.hash = "#/catalogo";
        return;
    }

    errorBox.textContent = "Usuario o contraseña incorrectos.";
    errorBox.style.display = "block";
}

document.addEventListener("click", (e) => {
    if (e.target && e.target.id === "login_btn") {
        e.preventDefault();
        validarLogin();
    }
});

