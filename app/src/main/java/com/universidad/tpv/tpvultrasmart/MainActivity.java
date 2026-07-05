package com.universidad.tpv.tpvultrasmart;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends Activity {

    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Inicializar Python y Flask en segundo plano
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }
        
        // Iniciar el servidor Flask local en un hilo para no congelar la app
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    Python py = Python.getInstance();
                    // Llama al archivo que arranca Flask (ej. server.py o app.py)
                    PyObject server = py.getModule("server"); 
                    server.callAttr("iniciar_servidor");
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }).start();

        // Configurar WebView para que abra el localhost:5000
        webView = new WebView(this);
        setContentView(webView);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        
        // Esperar 1 segundo a que Flask arranque y luego cargar la web
        webView.postDelayed(() -> {
            webView.loadUrl("http://127.0.0.1:5000/");
        }, 1000);
    }
}
