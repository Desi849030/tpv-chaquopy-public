/**
 * TPV Ultra Smart - Autenticación
 * Conecta con el servidor Flask vía API
 */
window.TPV_AUTH = {
    
    /**
     * Cargar usuarios desde archivo local (FALLBACK)
     */
    async cargarUsuarios() {
        try {
            const data = await fetch("/config/users.json").then(r => r.json());
            return data;
        } catch (e) {
            console.error("Error cargando users.json", e);
            return null;
        }
    },

    /**
     * Login contra el servidor (PROFESIONAL)
     */
    async loginAPI(usuario, password) {
        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ usuario, clave: password })
            });
            
            const data = await res.json();
            
            if (data.status === 'ok') {
                this.guardarSesion(usuario, data.role, data.nombre);
                return { success: true, role: data.role, nombre: data.nombre };
            } else {
                return { success: false, error: data.error || 'Credenciales incorrectas' };
            }
        } catch (e) {
            console.error("Error en login API:", e);
            console.warn("Servidor no disponible, usando login local...");
            return this.loginLocal(usuario, password);
        }
    },

    /**
     * Login local (FALLBACK sin servidor)
     */
    async loginLocal(usuario, password) {
        const data = await this.cargarUsuarios();
        if (!data) {
            return { success: false, error: "No se pudo cargar configuracion" };
        }

        if (usuario === data.desarrollador.usuario && password === data.desarrollador.password) {
            this.guardarSesion(usuario, "desarrollador", "Desarrollador");
            return { success: true, role: "desarrollador", nombre: "Desarrollador" };
        }

        const admin = data.administradores.find(a => a.usuario === usuario && a.password === password);
        if (admin) {
            this.guardarSesion(usuario, "administrador", admin.nombre);
            return { success: true, role: "administrador", nombre: admin.nombre };
        }

        const emp = data.empleados.find(e => e.usuario === usuario && e.password === password);
        if (emp) {
            this.guardarSesion(usuario, "empleado", emp.nombre);
            return { success: true, role: "empleado", nombre: emp.nombre };
        }

        const cli = data.clientes.find(c => c.usuario === usuario && c.password === password);
        if (cli) {
            this.guardarSesion(usuario, "cliente", cli.nombre);
            return { success: true, role: "cliente", nombre: cli.nombre };
        }

        return { success: false, error: "Usuario o contrasena incorrectos" };
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
