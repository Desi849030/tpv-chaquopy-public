package com.universidad.tpv.tpvultrasmart;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends Activity {
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }
        
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    File modeloFile = new File(getFilesDir(), "qwen-coder.gguf");
                    if (!modeloFile.exists()) {
                        runOnUiThread(() -> setContentView(R.layout.activity_main));
                        URL url = new URL("https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q5_k_m.gguf");
                        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                        conn.connect();
                        InputStream input = conn.getInputStream();
                        FileOutputStream output = new FileOutputStream(modeloFile);
                        byte data[] = new byte[8192];
                        int count;
                        while ((count = input.read(data)) != -1) {
                            output.write(data, 0, count);
                        }
                        output.flush(); output.close(); input.close();
                    }
                    
                    Python py = Python.getInstance();
                    PyObject server = py.getModule("patch_ai");
                    server.callAttr("iniciar_servidor");
                    
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }).start();

        webView = new WebView(this);
        setContentView(webView);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        webView.postDelayed(() -> webView.loadUrl("http://127.0.0.1:5050/"), 2000);
    }
}
