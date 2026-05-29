/**
 * TPV Ultra Smart - Autenticación
 * Conecta con el servidor Flask vía API
 */
window.TPV_AUTH = {

    /**
     * Login contra el servidor (PROFESIONAL)
     */
    async loginAPI(usuario, password) {
        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ usuario: usuario, clave: password })
            });

            const data = await res.json();

            // El backend devuelve token y usuario si es exitoso
            if (data.token || data.status === 'ok') {
                const rol = data.usuario?.rol || data.role || 'empleado';
                const nombre = data.usuario?.nombre || data.nombre || usuario;
                
                this.guardarSesion(usuario, rol, nombre);
                return { success: true, role: rol, nombre: nombre };
            } else {
                return { success: false, error: data.error || data.mensaje || 'Credenciales incorrectas' };
            }
        } catch (e) {
            console.error("Error en login API:", e);
            return { success: false, error: "Error de conexión con el servidor" };
        }
    },

    guardarSesion(usuario, rol, nombre) {
        localStorage.setItem("tpv_usuario", usuario);
        localStorage.setItem("tpv_rol", rol);
        localStorage.setItem("tpv_nombre", nombre || usuario);
        localStorage.setItem("tpv_login_time", Date.now().toString());
    },

    cerrarSesion() {
        localStorage.removeItem("tpv_usuario");
        localStorage.removeItem("tpv_rol");
        localStorage.removeItem("tpv_nombre");
        localStorage.removeItem("tpv_login_time");
    },

    obtenerRol() {
        return localStorage.getItem("tpv_rol");
    },

    obtenerUsuario() {
        return localStorage.getItem("tpv_usuario");
    },

    obtenerNombre() {
        return localStorage.getItem("tpv_nombre") || this.obtenerUsuario();
    },

    haySesion() {
        const usuario = this.obtenerUsuario();
        const rol = this.obtenerRol();
        return !!(usuario && rol);
    },

    obtenerSesion() {
        return {
            usuario: this.obtenerUsuario(),
            rol: this.obtenerRol(),
            nombre: this.obtenerNombre(),
            tiempoLogin: parseInt(localStorage.getItem("tpv_login_time") || "0")
        };
    }
};
