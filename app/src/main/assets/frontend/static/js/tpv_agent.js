window.TPV_AGENT = {
    mostrar(texto) {
        let barra = document.getElementById("tpv-agent");

        if (!barra) {
            barra = document.createElement("div");
            barra.id = "tpv-agent";
            barra.style.background = "#0d6efd";
            barra.style.color = "white";
            barra.style.padding = "0.9rem";
            barra.style.margin = "0.9rem";
            barra.style.borderRadius = "0.7rem";
            barra.style.fontWeight = "600";
            barra.style.fontSize = "0.95rem";
            barra.style.boxShadow = "0 4px 14px rgba(0,0,0,0.2)";
            document.body.prepend(barra);
        }

        barra.textContent = texto;
    },

    saludoInvitado() {
        this.mostrar("👋 Hola usuario, soy tu asistente del TPV. Puedo ayudarte a buscar productos, ver precios o saber en qué tienda hay stock.");
    },

    saludoPorRol(rol, usuario) {
        const mensajes = {
            desarrollador: `👨‍💻 Bienvenido ${usuario}. Modo desarrollador activo.`,
            administrador: `📊 Hola ${usuario}. Gestión administrativa lista.`,
            empleado: `🛒 Hola ${usuario}. La tienda está lista.`,
            cliente: `😊 Bienvenido ${usuario}. Explora el catálogo.`
        };
        this.mostrar(mensajes[rol] || `Hola ${usuario}.`);
    },

    async buscarProducto(nombre) {
        try {
            const res = await fetch(`/api/productos?query=${encodeURIComponent(nombre)}`);
            const data = await res.json();
            if (!data.length) return this.mostrar("No encontré ese producto.");
            const p = data[0];
            this.mostrar(`Producto: ${p.nombre} | Precio: ${p.precio}`);
        } catch {
            this.mostrar("Error consultando productos.");
        }
    }
};
