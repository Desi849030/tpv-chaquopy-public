import { tpvInit } from "./tpv_init.js";
import "./tpv_agent.js";
import "./tpv_auth.js";

async function tpvBoot() {
    console.log("🚀 Booting TPV...");

    await tpvInit();

    const splash = document.getElementById("splash");
    const login = document.getElementById("login");
    const app = document.getElementById("app");

    splash.style.display = "flex";
    login.style.display = "none";
    app.style.display = "none";

    await new Promise(res => setTimeout(res, 1200));

    splash.style.display = "none";

    const rol = TPV_AUTH.obtenerRol();
    const usuario = TPV_AUTH.obtenerUsuario();

    if (!rol) {
        login.style.display = "flex";
        TPV_AGENT.saludoInvitado();
    } else {
        app.style.display = "block";
        TPV_AGENT.saludoPorRol(rol, usuario);
    }
}

document.addEventListener("DOMContentLoaded", tpvBoot);

