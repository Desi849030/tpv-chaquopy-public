package com.tpv.pos;

import android.content.Context;
import android.content.SharedPreferences;
import android.hardware.biometrics.BiometricPrompt;
import android.os.Build;
import android.util.Log;
import androidx.annotation.RequiresApi;
import java.util.concurrent.Executor;

/**
 * AuthManager — Centraliza la autenticacion (biometrica, PIN, sesion).
 * Maneja credenciales, sesiones activas y tiempo de inactividad.
 */
public class AuthManager {
    private static final String TAG = "TPV.Auth";
    private static final String PREFS_NAME = "tpv_auth_prefs";
    private static final String KEY_SESSION_TOKEN = "session_token";
    private static final String KEY_SESSION_EXPIRY = "session_expiry";
    private static final String KEY_REMEMBER_USER = "remember_user";
    private static final String KEY_BIOMETRIC_ENABLED = "biometric_enabled";
    private static final long SESSION_TIMEOUT_MS = 8 * 60 * 60 * 1000; // 8 horas

    private final SharedPreferences prefs;
    private String currentSessionToken = null;
    private OnAuthListener authListener;

    public interface OnAuthListener {
        void onAuthSuccess(String sessionToken);
        void onAuthFailure(String reason);
        void onSessionExpired();
    }

    public AuthManager(Context context) {
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    /**
     * Verifica si hay una sesion activa y valida.
     */
    public boolean hasActiveSession() {
        String token = prefs.getString(KEY_SESSION_TOKEN, null);
        long expiry = prefs.getLong(KEY_SESSION_EXPIRY, 0);
        if (token == null) return false;
        if (System.currentTimeMillis() > expiry) {
            clearSession();
            if (authListener != null) authListener.onSessionExpired();
            return false;
        }
        currentSessionToken = token;
        return true;
    }

    /**
     * Crea una nueva sesion tras login exitoso.
     */
    public void createSession(String token) {
        SharedPreferences.Editor editor = prefs.edit();
        editor.putString(KEY_SESSION_TOKEN, token);
        editor.putLong(KEY_SESSION_EXPIRY, System.currentTimeMillis() + SESSION_TIMEOUT_MS);
        editor.apply();
        currentSessionToken = token;
        Log.i(TAG, "Sesion creada, expira en " + (SESSION_TIMEOUT_MS / 3600000) + "h");
    }

    /**
     * Cierra la sesion actual y limpia credenciales.
     */
    public void clearSession() {
        SharedPreferences.Editor editor = prefs.edit();
        editor.remove(KEY_SESSION_TOKEN);
        editor.remove(KEY_SESSION_EXPIRY);
        editor.apply();
        currentSessionToken = null;
        Log.i(TAG, "Sesion cerrada");
    }

    /**
     * Lanza autenticacion biometrica si esta disponible y habilitada.
     */
    @RequiresApi(api = Build.VERSION_CODES.P)
    public void authenticateWithBiometrics(Context activityCtx, Executor executor) {
        if (!isBiometricEnabled() || !canUseBiometrics()) {
            if (authListener != null) {
                authListener.onAuthFailure("Biometria no disponible o deshabilitada");
            }
            return;
        }

        BiometricPrompt prompt = new BiometricPrompt(
            (androidx.fragment.app.FragmentActivity) activityCtx,
            executor,
            new BiometricPrompt.AuthenticationCallback() {
                @Override
                public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult result) {
                    Log.i(TAG, "Biometria exitosa");
                    if (authListener != null) {
                        authListener.onAuthSuccess(currentSessionToken != null ?
                            currentSessionToken : "bio_" + System.currentTimeMillis());
                    }
                }

                @Override
                public void onAuthenticationFailed() {
                    Log.w(TAG, "Biometria fallida");
                    if (authListener != null) {
                        authListener.onAuthFailure("Autenticacion biometrica fallida");
                    }
                }

                @Override
                public void onAuthenticationError(int errorCode, CharSequence errString) {
                    Log.e(TAG, "Biometria error: " + errString);
                    if (authListener != null) {
                        authListener.onAuthFailure("Error: " + errString);
                    }
                }
            }
        );

        prompt.authenticate(new BiometricPrompt.PromptInfo.Builder()
            .setTitle("TPV Ultra Smart")
            .setSubtitle("Verificacion de identidad")
            .setDescription("Usa tu huella o rostro para acceder")
            .setNegativeButtonText("Cancelar")
            .build());
    }

    /**
     * Verifica si el dispositivo soporta biometria.
     */
    public boolean canUseBiometrics() {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.P;
    }

    public boolean isBiometricEnabled() {
        return prefs.getBoolean(KEY_BIOMETRIC_ENABLED, false);
    }

    public void setBiometricEnabled(boolean enabled) {
        prefs.edit().putBoolean(KEY_BIOMETRIC_ENABLED, enabled).apply();
    }

    public void setRememberUser(boolean remember) {
        prefs.edit().putBoolean(KEY_REMEMBER_USER, remember).apply();
    }

    public boolean isRememberUser() {
        return prefs.getBoolean(KEY_REMEMBER_USER, false);
    }

    public void setOnAuthListener(OnAuthListener listener) {
        this.authListener = listener;
    }

    public String getSessionToken() { return currentSessionToken; }
}
