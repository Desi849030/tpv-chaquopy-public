package com.universidad.tpv.tpvultrasmart;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends Activity {

    private TextView txtChat;
    private EditText txtInput;
    private Button btnSend;
    private ScrollView scrollView;
    private ProgressBar progressBar;
    private boolean iaLista = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        try {
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(this));
            }
        } catch (Exception e) {
            txtChat = findViewById(R.id.txtChat);
            txtChat.setText("Error fatal iniciando Python: " + e.getMessage());
            return;
        }

        txtChat = findViewById(R.id.txtChat);
        txtInput = findViewById(R.id.txtInput);
        btnSend = findViewById(R.id.btnSend);
        scrollView = findViewById(R.id.scrollView);
        progressBar = findViewById(R.id.progressBar);

        txtChat.setText("Inicializando IA en el dispositivo...\n");
        btnSend.setEnabled(false);

        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    Python py = Python.getInstance();
                    PyObject module = py.getModule("agente_apk");
                    
                    File modeloFile = new File(getFilesDir(), "qwen-coder.gguf");
                    
                    if (!modeloFile.exists()) {
                        runOnUiThread(() -> {
                            txtChat.append("Descargando modelo de IA (1.2 GB)...\n");
                            progressBar.setVisibility(ProgressBar.VISIBLE);
                            progressBar.setProgress(0);
                        });
                        
                        // Descarga nativa con progreso
                        URL url = new URL("https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q5_k_m.gguf");
                        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                        connection.connect();
                        
                        int fileLength = connection.getContentLength();
                        InputStream input = connection.getInputStream();
                        FileOutputStream output = new FileOutputStream(modeloFile);
                        
                        byte data[] = new byte[8192];
                        long total = 0;
                        int count;
                        
                        while ((count = input.read(data)) != -1) {
                            total += count;
                            final int progress = (int) (total * 100 / fileLength);
                            runOnUiThread(() -> progressBar.setProgress(progress));
                            output.write(data, 0, count);
                        }
                        
                        output.flush();
                        output.close();
                        input.close();
                        
                        runOnUiThread(() -> {
                            progressBar.setVisibility(ProgressBar.GONE);
                            txtChat.append("Descarga completada.\n");
                        });
                    }
                    
                    runOnUiThread(() -> txtChat.append("Cargando IA en RAM (10 segundos)...\n"));
                    PyObject result = module.callAttr("inicializar_ia", modeloFile.getAbsolutePath());
                    iaLista = true;
                    
                    runOnUiThread(() -> {
                        txtChat.append(result.toString() + "\n\nPuedes hablar con la IA:\n");
                        btnSend.setEnabled(true);
                    });
                } catch (final Exception e) {
                    runOnUiThread(() -> txtChat.append("Error: " + e.getMessage() + "\n"));
                }
            }
        }).start();

        btnSend.setOnClickListener(v -> {
            String pregunta = txtInput.getText().toString();
            if (!pregunta.isEmpty() && iaLista) {
                txtChat.append("\nTú: " + pregunta + "\n");
                txtInput.setText("");
                txtChat.append("IA: Pensando...\n");
                scrollView.post(() -> scrollView.fullScroll(ScrollView.FOCUS_DOWN));

                new Thread(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            Python py = Python.getInstance();
                            PyObject module = py.getModule("agente_apk");
                            PyObject respuesta = module.callAttr("procesar_pregunta", pregunta);
                            
                            runOnUiThread(() -> {
                                String textoActual = txtChat.getText().toString();
                                txtChat.setText(textoActual.replace("IA: Pensando...\n", "IA: " + respuesta.toString() + "\n"));
                                scrollView.post(() -> scrollView.fullScroll(ScrollView.FOCUS_DOWN));
                            });
                        } catch (final Exception e) {
                            runOnUiThread(() -> txtChat.append("Error procesando: " + e.getMessage() + "\n"));
                        }
                    }
                }).start();
            }
        });
    }
}
