window.TPV_ROLES = {
    permisos: {
        desarrollador: ["dashboard", "catalogo", "tienda", "admin"],
        administrador: ["dashboard", "catalogo", "tienda"],
        empleado: ["tienda"],
        cliente: ["catalogo"]
    },

    puedeAcceder(rol, vista) {
        return this.permisos[rol]?.includes(vista);
    }
};

