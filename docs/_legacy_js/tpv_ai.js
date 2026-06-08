export function sugerirProductos(carrito, inventario) {
    const ids = carrito.map(p => p.id);
    return inventario.filter(p => !ids.includes(p.id)).slice(0, 3);
}
