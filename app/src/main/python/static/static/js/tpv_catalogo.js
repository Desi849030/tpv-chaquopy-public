import { TPV_STATE, guardarEstado } from "./tpv_state.js";

export function cargarCatalogo() {
    // Demo temporal
    TPV_STATE.inventario = [
        { id: 1, nombre: "Producto A", precio: 10, stock: 20 },
        { id: 2, nombre: "Producto B", precio: 15, stock: 10 },
        { id: 3, nombre: "Producto C", precio: 8, stock: 50 }
    ];

    guardarEstado();
}

export function obtenerCatalogo() {
    return TPV_STATE.inventario;
}
