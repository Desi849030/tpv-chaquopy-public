package com.tpv.pos;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import androidx.core.content.ContextCompat;
import java.util.ArrayList;
import java.util.List;

/**
 * PermissionManager — Gestiona permisos del sistema de forma centralizada.
 * Simplifica la solicitud y verificacion de permisos peligrosos.
 */
public class PermissionManager {
    private static final String TAG = "TPV.Permissions";

    /**
     * Permisos necesarios para el funcionamiento completo del TPV.
     */
    public static final String[] REQUIRED_PERMISSIONS = {
        Manifest.permission.CAMERA,
        Manifest.permission.READ_EXTERNAL_STORAGE,
        Manifest.permission.WRITE_EXTERNAL_STORAGE,
    };

    /**
     * Permisos opcionales que mejoran la funcionalidad.
     */
    public static final String[] OPTIONAL_PERMISSIONS = {
        Manifest.permission.ACCESS_FINE_LOCATION,
        Manifest.permission.BLUETOOTH_CONNECT,
        Manifest.permission.RECORD_AUDIO,
    };

    private final Context context;
    private OnPermissionResultListener permissionListener;

    public interface OnPermissionResultListener {
        void onPermissionsGranted(List<String> granted);
        void onPermissionsDenied(List<String> denied);
        void onAllPermissionsGranted();
    }

    public PermissionManager(Context context) {
        this.context = context.getApplicationContext();
    }

    /**
     * Retorna los permisos que aun no han sido concedidos.
     */
    public List<String> getDeniedPermissions(String[] permissions) {
        List<String> denied = new ArrayList<>();
        for (String perm : permissions) {
            if (ContextCompat.checkSelfPermission(context, perm)
                    != PackageManager.PERMISSION_GRANTED) {
                denied.add(perm);
            }
        }
        return denied;
    }

    /**
     * Verifica si todos los permisos requeridos estan concedidos.
     */
    public boolean hasAllRequiredPermissions() {
        return getDeniedPermissions(REQUIRED_PERMISSIONS).isEmpty();
    }

    /**
     * Verifica un permiso individual.
     */
    public boolean hasPermission(String permission) {
        return ContextCompat.checkSelfPermission(context, permission)
                == PackageManager.PERMISSION_GRANTED;
    }

    /**
     * Retorna un arreglo con solo los permisos que faltan.
     * Usar para pasar a ActivityCompat.requestPermissions().
     */
    public String[] getMissingRequiredPermissions() {
        List<String> denied = getDeniedPermissions(REQUIRED_PERMISSIONS);
        return denied.toArray(new String[0]);
    }

    public void setOnPermissionResultListener(OnPermissionResultListener listener) {
        this.permissionListener = listener;
    }
}
