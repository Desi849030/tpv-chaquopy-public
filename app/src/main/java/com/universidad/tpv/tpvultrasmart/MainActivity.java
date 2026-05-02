package com.universidad.tpv.tpvultrasmart;

import android.Manifest;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.WindowManager;
import android.webkit.*;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.biometric.BiometricManager;
import androidx.biometric.BiometricPrompt;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.FragmentActivity;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.concurrent.Executor;

public class MainActivity extends FragmentActivity {
    private static final int FILE_CHOOSER_REQUEST = 1;
    private static final int CAMERA_PERMISSION_REQUEST = 100;
    private ValueCallback<Uri[]> filePathCallback;
    private WebView webView;
    private boolean cameraPermissionGranted = false;
    private BiometricPrompt biometricPrompt;
    private Executor executor;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(android.view.Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN);
        if (!Python.isStarted()) Python.start(new AndroidPlatform(this));
        String filesDir = getFilesDir().getAbsolutePath();
        System.setProperty("TPV_FILES_DIR", filesDir);
        String frontendDir = filesDir + "/frontend";
        copyAssets("frontend", frontendDir);
        System.setProperty("TPV_FRONTEND_DIR", frontendDir);
        FrameLayout splashRoot = new FrameLayout(this);
        splashRoot.setBackgroundColor(Color.parseColor("#0a0e1a"));
        LinearLayout splash = new LinearLayout(this);
        splash.setOrientation(LinearLayout.VERTICAL);
        splash.setGravity(Gravity.CENTER);
        splash.setLayoutParams(new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.MATCH_PARENT));
        TextView logo = new TextView(this);
        logo.setText("TPV"); logo.setTextSize(52f); logo.setTextColor(Color.WHITE);
        logo.setGravity(Gravity.CENTER); logo.setTypeface(null, android.graphics.Typeface.BOLD);
        logo.setLetterSpacing(0.1f);
        TextView sub = new TextView(this);
        sub.setText("Ultra Smart"); sub.setTextSize(15f);
        sub.setTextColor(Color.parseColor("#64748b")); sub.setGravity(Gravity.CENTER);
        sub.setPadding(0, 6, 0, 0);
        TextView loading = new TextView(this);
        loading.setText("Cargando..."); loading.setTextSize(12f);
        loading.setTextColor(Color.parseColor("#475569")); loading.setGravity(Gravity.CENTER);
        loading.setPadding(0, 24, 0, 0);
        splash.addView(logo); splash.addView(sub); splash.addView(loading);
        splashRoot.addView(splash); setContentView(splashRoot);
        executor = ContextCompat.getMainExecutor(this);
        initBiometricPrompt();
        requestCameraPermission();
        Python py = Python.getInstance();
        py.getModule("start_server");
        new Thread(() -> {
            for (int i = 0; i < 40; i++) {
                try {
                    java.net.HttpURLConnection conn = (java.net.HttpURLConnection)
                        new java.net.URL("http://127.0.0.1:5050/api/health").openConnection();
                    conn.setConnectTimeout(300); conn.setReadTimeout(300);
                    int code = conn.getResponseCode(); conn.disconnect();
                    if (code == 200 || code == 401 || code == 404) break;
                } catch (Exception e) {}
                try { Thread.sleep(250); } catch (Exception ex) {}
            }
            runOnUiThread(() -> setupWebView());
        }).start();
    }

    private void initBiometricPrompt() {
        biometricPrompt = new BiometricPrompt(this, executor,
            new BiometricPrompt.AuthenticationCallback() {
                @Override public void onAuthenticationError(int errorCode, @NonNull CharSequence errString) {
                    notifyWebView(false, "Error: " + errString);
                }
                @Override public void onAuthenticationSucceeded(@NonNull BiometricPrompt.AuthenticationResult result) {
                    notifyWebView(true, "Autenticacion biometrica exitosa");
                }
                @Override public void onAuthenticationFailed() {
                    notifyWebView(false, "Autenticacion fallida. Intenta de nuevo.");
                }
            });
    }

    private void notifyWebView(boolean success, String message) {
        if (webView != null) {
            String safeMsg = message.replace("'", "\\'");
            String js = "if(window.onBiometricCallback)window.onBiometricCallback({success:" + success + ",message:'" + safeMsg + "'})";
            runOnUiThread(() -> webView.evaluateJavascript(js, null));
        }
    }

    private void requestCameraPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                cameraPermissionGranted = true;
            } else {
                if (shouldShowRequestPermissionRationale(Manifest.permission.CAMERA)) {
                    new AlertDialog.Builder(this)
                        .setTitle("Permiso de Camara")
                        .setMessage("TPV Ultra Smart necesita la camara para el escaner QR.")
                        .setPositiveButton("Permitir", (d, w) -> requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_REQUEST))
                        .setNegativeButton("Cancelar", null).show();
                } else {
                    requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_REQUEST);
                }
            }
        } else { cameraPermissionGranted = true; }
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == CAMERA_PERMISSION_REQUEST) {
            cameraPermissionGranted = grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED;
        }
    }

    private void setupWebView() {
        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#0a0e1a"));
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true); s.setAllowContentAccess(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setCacheMode(WebSettings.LOAD_NO_CACHE);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        webView.addJavascriptInterface(new TpvNativeBridge(), "TPVNative");
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onJsAlert(WebView v, String u, String m, JsResult r) { mostrarAlertDialog(m, r); return true; }
            @Override public boolean onJsConfirm(WebView v, String u, String m, JsResult r) { mostrarConfirmDialog(m, r); return true; }
            @Override public boolean onShowFileChooser(WebView wv, ValueCallback<Uri[]> fpc, WebChromeClient.FileChooserParams fcp) {
                filePathCallback = fpc;
                Intent i = new Intent(Intent.ACTION_GET_CONTENT);
                i.setType("*/*"); i.addCategory(Intent.CATEGORY_OPENABLE);
                startActivityForResult(Intent.createChooser(i, "Seleccionar archivo"), FILE_CHOOSER_REQUEST);
                return true;
            }
            @Override
            public void onPermissionRequest(final android.webkit.PermissionRequest request) {
                runOnUiThread(() -> {
                    if (cameraPermissionGranted) request.grant(request.getResources());
                    else request.deny();
                });
            }
        });
        webView.setWebViewClient(new WebViewClient());
        webView.clearCache(true); webView.clearHistory();
        setContentView(webView);
        webView.loadUrl("http://127.0.0.1:5050");
    }

    // ═══ JAVASCRIPT BRIDGE ═══
    public class TpvNativeBridge {
        @android.webkit.JavascriptInterface
        public String getBiometricStatus() {
            if (Build.VERSION.SDK_INT < 23) return "{'supported':false,'status':'NOT_AVAILABLE','methods':[]}";
            int status = BiometricManager.from(MainActivity.this).canAuthenticate();
            String s; boolean ok;
            switch (status) {
                case BiometricManager.BIOMETRIC_SUCCESS: s = "READY"; ok = true; break;
                case BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE: s = "NO_HARDWARE"; ok = false; break;
                case BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE: s = "HW_UNAVAILABLE"; ok = false; break;
                case BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED: s = "NOT_ENROLLED"; ok = true; break;
                default: s = "UNKNOWN"; ok = false;
            }
            return "{'supported':" + ok + ",'status':'" + s + "','methods':['fingerprint','face'],'sdk':" + Build.VERSION.SDK_INT + "}";
        }
        @android.webkit.JavascriptInterface
        public boolean canAuthenticate() {
            if (Build.VERSION.SDK_INT < 23) return false;
            return BiometricManager.from(MainActivity.this).canAuthenticate() == BiometricManager.BIOMETRIC_SUCCESS;
        }
        @android.webkit.JavascriptInterface
        public void authenticate(String title, String subtitle, String desc) {
            runOnUiThread(() -> {
                BiometricPrompt.PromptInfo.Builder b = new BiometricPrompt.PromptInfo.Builder()
                    .setTitle(title != null ? title : "TPV Ultra Smart")
                    .setSubtitle(subtitle != null ? subtitle : "Verificacion de identidad")
                    .setDescription(desc != null ? desc : "Usa tu huella o rostro")
                    .setNegativeButtonText("Cancelar");
                if (Build.VERSION.SDK_INT >= 30) {
                    try { b.setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG | BiometricManager.Authenticators.DEVICE_CREDENTIAL); }
                    catch (Exception ignored) {}
                }
                biometricPrompt.authenticate(b.build());
            });
        }
        @android.webkit.JavascriptInterface
        public String getDeviceInfo() {
            return "{'sdk':" + Build.VERSION.SDK_INT + ",'model':'" + Build.MODEL + "','brand':'" + Build.BRAND + "'}";
        }
        @android.webkit.JavascriptInterface public void vibrate(int ms) {
            if (Build.VERSION.SDK_INT >= 26) {
                android.os.Vibrator v = (android.os.Vibrator) getSystemService(VIBRATOR_SERVICE);
                if (v != null && v.hasVibrator()) v.vibrate(android.os.VibrationEffect.createOneShot(Math.max(1, ms), android.os.VibrationEffect.DEFAULT_AMPLITUDE));
            }
        }
        @android.webkit.JavascriptInterface public void showToast(String msg) { runOnUiThread(() -> android.widget.Toast.makeText(MainActivity.this, msg, android.widget.Toast.LENGTH_SHORT).show()); }
        @android.webkit.JavascriptInterface public boolean isCameraGranted() { return cameraPermissionGranted; }
        @android.webkit.JavascriptInterface public String getAppVersion() {
            try { return getPackageManager().getPackageInfo(getPackageName(), 0).versionName; } catch (Exception e) { return "unknown"; }
        }
    }

    @Override protected void onActivityResult(int r, int resultCode, Intent data) {
        if (r == FILE_CHOOSER_REQUEST && filePathCallback != null) {
            Uri[] res = null;
            if (resultCode == RESULT_OK && data != null && data.getData() != null) res = new Uri[]{data.getData()};
            filePathCallback.onReceiveValue(res); filePathCallback = null;
        }
        super.onActivityResult(r, resultCode, data);
    }
    @Override public void onBackPressed() { if (webView != null && webView.canGoBack()) webView.goBack(); else moveTaskToBack(true); }
    @Override protected void onDestroy() { if (webView != null) { webView.stopLoading(); webView.destroy(); } super.onDestroy(); }

    private void clearDir(File d) { if (d == null || !d.exists()) return; File[] fs = d.listFiles(); if (fs != null) for (File f : fs) { if (f.isDirectory()) clearDir(f); else f.delete(); } }
    private void copyAssets(String ap, String dp) {
        try {
            String[] files = getAssets().list(ap); if (files == null) return;
            File dest = new File(dp); if (!dest.exists()) dest.mkdirs(); else { clearDir(dest); dest.mkdirs(); }
            for (String fn : files) {
                String src = ap + "/" + fn, dst = dp + "/" + fn;
                String[] sub = getAssets().list(src);
                if (sub != null && sub.length > 0) copyAssets(src, dst);
                else { InputStream in = getAssets().open(src); File out = new File(dst); out.delete();
                    OutputStream o = new FileOutputStream(out); byte[] buf = new byte[4096]; int l;
                    while ((l = in.read(buf)) > 0) o.write(buf, 0, l); in.close(); o.close(); }
            }
        } catch (Exception e) { e.printStackTrace(); }
    }
    private AlertDialog dialogActual;
    private void mostrarConfirmDialog(String message, JsResult result) {
        LinearLayout root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(60,50,60,40);
        GradientDrawable bg = new GradientDrawable(); bg.setColor(Color.WHITE); bg.setCornerRadius(32f); root.setBackground(bg);
        TextView icon = new TextView(this); icon.setText("!?"); icon.setTextSize(36f); icon.setGravity(Gravity.CENTER); root.addView(icon);
        TextView msg = new TextView(this); msg.setText(message); msg.setTextSize(16f); msg.setTextColor(Color.parseColor("#1a1a2e")); msg.setGravity(Gravity.CENTER); msg.setPadding(0,20,0,20); root.addView(msg);
        LinearLayout btns = new LinearLayout(this); btns.setOrientation(LinearLayout.HORIZONTAL); btns.setGravity(Gravity.CENTER);
        Button cancel = new Button(this); cancel.setText("Cancelar"); cancel.setTextColor(Color.parseColor("#6c757d")); cancel.setTextSize(15f); btns.addView(cancel);
        Button accept = new Button(this); accept.setText("Aceptar"); accept.setTextColor(Color.WHITE); accept.setTextSize(15f);
        GradientDrawable bb = new GradientDrawable(); bb.setColor(Color.parseColor("#0d6efd")); bb.setCornerRadius(24f); accept.setBackground(bb); btns.addView(accept);
        root.addView(btns);
        dialogActual = new AlertDialog.Builder(this).setView(root).setCancelable(false).create();
        dialogActual.getWindow().setBackgroundDrawableResource(android.R.drawable.screen_background_dark_transparent);
        cancel.setOnClickListener(v -> { result.cancel(); dialogActual.dismiss(); });
        accept.setOnClickListener(v -> { result.confirm(); dialogActual.dismiss(); }); dialogActual.show();
    }
    private void mostrarAlertDialog(String message, JsResult result) {
        LinearLayout root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(60,50,60,40);
        GradientDrawable bg = new GradientDrawable(); bg.setColor(Color.WHITE); bg.setCornerRadius(32f); root.setBackground(bg);
        TextView msg = new TextView(this); msg.setText(message); msg.setTextSize(16f); msg.setTextColor(Color.parseColor("#1a1a2e")); msg.setGravity(Gravity.CENTER); msg.setPadding(0,10,0,10); root.addView(msg);
        Button ok = new Button(this); ok.setText("OK"); ok.setTextColor(Color.WHITE);
        GradientDrawable bb = new GradientDrawable(); bb.setColor(Color.parseColor("#0d6efd")); bb.setCornerRadius(24f); ok.setBackground(bb);
        LinearLayout btns = new LinearLayout(this); btns.setGravity(Gravity.CENTER); btns.addView(ok); root.addView(btns);
        dialogActual = new AlertDialog.Builder(this).setView(root).setCancelable(false).create();
        dialogActual.getWindow().setBackgroundDrawableResource(android.R.drawable.screen_background_dark_transparent);
        ok.setOnClickListener(v -> { result.confirm(); dialogActual.dismiss(); }); dialogActual.show();
    }
}
