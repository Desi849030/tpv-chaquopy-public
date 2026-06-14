/**
 * TPV Ultra Smart - Agente Asistente IA
 * Profesionalizado con conexion al servidor
 */
window.TPV_AGENT = {
    
    mostrar(texto) {
        let barra = document.getElementById("tpv-agent");

        if (!barra) {
            barra = document.createElement("div");
            barra.id = "tpv-agent";
            barra.style.cssText = [
                "background: linear-gradient(135deg, #3b82f6, #8b5cf6)",
                "color: white",
                "padding: 14px 20px",
                "margin: 10px",
                "border-radius: 12px",
                "font-weight: 600",
                "font-size: 14px",
                "box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3)",
                "display: flex",
                "align-items: center",
                "gap: 10px",
                "z-index: 9999"
            ].join(";");
            document.body.prepend(barra);
        }

        barra.innerHTML = "<span style='font-size:20px;'>🤖</span><span>" + texto + "</span>";
        barra.style.display = "flex";
    },

    ocultar() {
        const barra = document.getElementById("tpv-agent");
        if (barra) barra.style.display = "none";
    },

    saludoInvitado() {
        this.mostrar("Hola! Soy tu asistente del TPV. Puedo ayudarte a buscar productos, ver precios o consultar stock.");
    },

    saludoPorRol(rol, usuario) {
        const mensajes = {
            desarrollador: "Bienvenido " + usuario + ". Modo desarrollador activo.",
            administrador: "Hola " + usuario + ". Panel de administracion listo.",
            empleado: "Hola " + usuario + ". La tienda esta lista para vender.",
            cliente: "Bienvenido " + usuario + ". Explora nuestro catalogo de productos."
        };
        this.mostrar(mensajes[rol] || "Hola " + usuario + ", bienvenido.");
    },

    async buscarProducto(nombre) {
        try {
            const res = await fetch("/api/productos?query=" + encodeURIComponent(nombre));
            const data = await res.json();
            
            if (!data.productos || data.productos.length === 0) {
                return this.mostrar("No encontre ese producto. Intenta con otro nombre.");
            }
            
            const p = data.productos[0];
            this.mostrar(p.nombre + " | Precio: $" + (p.precio || 0).toFixed(2) + " | Stock: " + (p.stock_actual || "N/A"));
        } catch (e) {
            console.error("Error buscando producto:", e);
            this.mostrar("Error consultando productos. Verifica tu conexion.");
        }
    },

    async consultarStock() {
        try {
            const res = await fetch("/api/stock");
            const data = await res.json();
            
            this.mostrar(
                "Inventario: " + data.total + " productos | " +
                "Stock bajo: " + (data.agotados || 0) + " | " +
                "Valor: $" + (data.valor_total || 0).toFixed(2)
            );
        } catch (e) {
            console.error("Error consultando stock:", e);
            this.mostrar("Error consultando inventario.");
        }
    },

    async chat(mensaje) {
        const rol = TPV_AUTH.obtenerRol() || "cliente";
        const usuario = TPV_AUTH.obtenerUsuario() || "Usuario";
        
        try {
            const res = await fetch("/api/agent/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    message: mensaje, 
                    role: rol,
                    nombre: usuario
                })
            });
            
            const data = await res.json();
            return data.response || data.error || "Sin respuesta";
        } catch (e) {
            console.error("Error en chat:", e);
            return "Error de conexion con el servidor.";
        }
    }
};
