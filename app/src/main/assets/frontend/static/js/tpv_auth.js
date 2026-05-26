window.TPV_AUTH = {
    async cargarUsuarios() {
        try {
            const data = await fetch("/config/users.json").then(r => r.json());
            return data;
        } catch (e) {
            console.error("Error cargando users.json", e);
            return null;
        }
    },

    guardarSesion(usuario, rol) {
        localStorage.setItem("tpv_usuario", usuario);
        localStorage.setItem("tpv_rol", rol);
    },

    cerrarSesion() {
        localStorage.removeItem("tpv_usuario");
        localStorage.removeItem("tpv_rol");
    },

    obtenerRol() {
        return localStorage.getItem("tpv_rol");
    },

    obtenerUsuario() {
        return localStorage.getItem("tpv_usuario");
    }
};
