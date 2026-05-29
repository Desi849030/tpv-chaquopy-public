/**
 * TPV Ultra Smart - Boot CON DEBUG VISUAL
 */
(function() {
    "use strict";

    if (window.__TPV_BOOT_EJECUTADO) return;
    window.__TPV_BOOT_EJECUTADO = true;

    // Crear div de debug visible
    var debugDiv = document.createElement("div");
    debugDiv.style.cssText = "position:fixed;top:0;left:0;right:0;background:red;color:white;padding:10px;z-index:99999;font-size:12px;";
    document.body.appendChild(debugDiv);

    function log(msg) {
        console.log(msg);
        debugDiv.innerHTML += msg + "<br>";
    }

    log("=== BOOT: Script cargado ===");

    function mostrarLogin() {
        log("=== BOOT: Ejecutando mostrarLogin()");
        var splash = document.getElementById("splash");
        var login = document.getElementById("login");
        log("splash=" + splash + " login=" + login);
        if (splash) splash.style.display = "none";
        if (login) login.style.display = "block";
        debugDiv.style.background = "green";
        log("=== BOOT: Login DEBERIA estar visible ===");
    }

    async function boot() {
        log("=== BOOT: boot() iniciado ===");

        // Verificar TPV_AUTH
        log("typeof TPV_AUTH = " + typeof TPV_AUTH);

        if (typeof TPV_AUTH === "undefined") {
            log("=== BOOT: TPV_AUTH NO definido -> login");
            mostrarLogin();
            return;
        }

        try {
            var res = await fetch("/api/health");
            log("API health OK");

            if (TPV_AUTH.haySesion()) {
                log("Hay sesion -> app");
                document.getElementById("splash").style.display = "none";
                document.getElementById("login").style.display = "none";
                document.getElementById("app").style.display = "block";
            } else {
                log("No hay sesion -> login");
                mostrarLogin();
            }
        } catch (e) {
            log("ERROR: " + e.message);
            mostrarLogin();
        }
    }

    // Ejecutar
    setTimeout(boot, 1000);
})();
