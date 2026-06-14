import { STORAGE_KEYS } from "./tpv_constants.js";

export const TPV_STATE = {
    usuario: null,
    carrito: [],
    inventario: [],
    pedidos: [],
    config: {},
    cargado: false
};

export function cargarEstado() {
    try {
        const data = localStorage.getItem(STORAGE_KEYS.STATE);
        if (data) Object.assign(TPV_STATE, JSON.parse(data));
    } catch (e) {
        console.error("Error cargando estado:", e);
    }
}

export function guardarEstado() {
    localStorage.setItem(STORAGE_KEYS.STATE, JSON.stringify(TPV_STATE));
}
