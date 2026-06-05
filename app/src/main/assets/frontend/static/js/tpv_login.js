/**
 * TPV Ultra Smart - Modulo de Login
 * Profesionalizado con conexion al servidor
 */

function login() {
    const user = document.getElementById("user");
    const pass = document.getElementById("pass");
    const errBox = document.getElementById("err");
    const errMsg = document.getElementById("errmsg");
    const btnLogin = document.getElementById("btnLogin");

    if (!user || !pass) return;
    
    const usuario = user.value.trim();
    const password = pass.value.trim();

    if (!usuario || !password) {
        mostrarError("Por favor, completa todos los campos.");
        return;
    }

    if (btnLogin) {
        btnLogin.disabled = true;
        btnLogin.textContent = "Verificando...";
    }

    TPV_AUTH.loginAPI(usuario, password).then(resultado => {
        if (resultado.success) {
            console.log("Login exitoso: " + resultado.nombre + " (" + resultado.role + ")");
            mostrarApp();
            TPV_AGENT.saludoPorRol(resultado.role, resultado.nombre);
            
            const rutas = {
                desarrollador: "#/dashboard",
                administrador: "#/dashboard",
                empleado: "#/tienda",
                cliente: "#/catalogo"
            };
            
            window.location.hash = rutas[resultado.role] || "#/catalogo";
        } else {
            mostrarError(resultado.error || "Credenciales incorrectas");
        }
    }).catch(e => {
        console.error("Error en login:", e);
        mostrarError("Error de conexion. Intenta de nuevo.");
    }).finally(() => {
        if (btnLogin) {
            btnLogin.disabled = false;
            btnLogin.textContent = "Entrar";
        }
    });
}

function mostrarError(mensaje) {
    const errBox = document.getElementById("err");
    const errMsg = document.getElementById("errmsg");
    if (errBox && errMsg) {
        errMsg.textContent = mensaje;
        errBox.style.display = "flex";
    }
}

function mostrarApp() {
    const loginDiv = document.getElementById("login");
    const appDiv = document.getElementById("app");
    if (loginDiv) loginDiv.style.display = "none";
    if (appDiv) appDiv.style.display = "block";
}

function mostrarLogin() {
    const splash = document.getElementById("splash");
    const loginDiv = document.getElementById("login");
    if (splash) splash.style.display = "none";
    if (loginDiv) loginDiv.style.display = "block";
}

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("pass").addEventListener("keypress", function(e) {
        if (e.key === "Enter") login();
    });
    
    document.getElementById("btnLogin").addEventListener("click", login);
    
    const pwToggle = document.getElementById("pwToggle");
    const passInput = document.getElementById("pass");
    if (pwToggle && passInput) {
        pwToggle.addEventListener("click", function() {
            passInput.type = passInput.type === "password" ? "text" : "password";
        });
    }
    
    setTimeout(mostrarLogin, 1500);
});
