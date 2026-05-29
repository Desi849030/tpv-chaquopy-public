import { TPV_STATE } from "./tpv_state.js";

export function obtenerResumen() {
    return {
        totalProductos: TPV_STATE.inventario.length,
        totalVentas: TPV_STATE.pedidos.length,
        totalCarrito: TPV_STATE.carrito.reduce((acc, p) => acc + p.cantidad, 0)
    };
}
