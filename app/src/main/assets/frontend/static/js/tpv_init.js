import { initRouter } from "./tpv_router.js";

export async function tpvInit() {
    console.log("🔧 Cargando layout...");

    const layout = await fetch("/templates/index.html").then(r => r.text());
    document.body.innerHTML = layout;

    initRouter();

    console.log("✔️ Layout cargado");
}
