import { TPV_STATE, guardarEstado } from "./tpv_state.js";

export function actualizarStock(idProducto, cantidad) {
    const producto = TPV_STATE.inventario.find(p => p.id === idProducto);
    if (!producto) return false;

    producto.stock = cantidad;
    guardarEstado();
    return true;
}

export function obtenerInventario() {
    return TPV_STATE.inventario;
}
