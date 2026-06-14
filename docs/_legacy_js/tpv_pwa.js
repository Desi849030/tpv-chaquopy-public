export function registrarPWA() {
    if ("serviceWorker" in navigator) {
        navigator.serviceWorker.register("/service-worker.js")
            .then(() => console.log("PWA registrada"))
            .catch(err => console.error("Error PWA:", err));
    }
}
