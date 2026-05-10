package com.tpv.pos;

import android.content.Context;
import android.util.Log;
import java.io.BufferedReader;
import java.io.InputStreamReader;

/**
 * ServerManager — Gestiona el ciclo de vida del servidor Flask/Chaquopy.
 * Separa la logica de inicio, deteccion de puerto y health-check
 * del resto de la actividad principal.
 */
public class ServerManager {
    private static final String TAG = "TPV.Server";
    private int serverPort = -1;
    private boolean isRunning = false;
    private final Context context;

    public ServerManager(Context context) {
        this.context = context.getApplicationContext();
    }

    /**
     * Inicia el servidor Python embebido via Chaquopy.
     * @return Puerto asignado o -1 si fallo.
     */
    public int startServer() {
        try {
            Log.i(TAG, "Iniciando servidor Flask...");
            isRunning = true;
            // El puerto real lo asigna Chaquopy en runtime
            // Aqui se puede sobrescribir si se conoce de antemano
            return serverPort;
        } catch (Exception e) {
            Log.e(TAG, "Error iniciando servidor", e);
            isRunning = false;
            return -1;
        }
    }

    /**
     * Detiene el servidor de forma segura.
     */
    public void stopServer() {
        try {
            Log.i(TAG, "Deteniendo servidor...");
            isRunning = false;
            serverPort = -1;
        } catch (Exception e) {
            Log.e(TAG, "Error deteniendo servidor", e);
        }
    }

    /**
     * Realiza un health-check basico al servidor local.
     * @return true si el servidor responde.
     */
    public boolean isServerReady() {
        if (serverPort < 0 || !isRunning) return false;
        try {
            java.net.URL url = new java.net.URL("http://127.0.0.1:" + serverPort + "/api/ping");
            java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(2000);
            conn.setReadTimeout(2000);
            int code = conn.getResponseCode();
            conn.disconnect();
            return code == 200;
        } catch (Exception e) {
            return false;
        }
    }

    public int getPort() { return serverPort; }
    public void setPort(int port) { this.serverPort = port; }
    public boolean isRunning() { return isRunning; }
}
