import { TPV_STATE, guardarEstado } from "./tpv_state.js";

export function agregarAlCarrito(idProducto, cantidad = 1) {
    const producto = TPV_STATE.inventario.find(p => p.id === idProducto);
    if (!producto) return false;

    const item = TPV_STATE.carrito.find(p => p.id === idProducto);

    if (item) {
        item.cantidad += cantidad;
    } else {
        TPV_STATE.carrito.push({
            id: producto.id,
            nombre: producto.nombre,
            precio: producto.precio,
            cantidad
        });
    }

    guardarEstado();
    return true;
}

export function obtenerCarrito() {
    return TPV_STATE.carrito;
}

export function limpiarCarrito() {
    TPV_STATE.carrito = [];
    guardarEstado();
}
