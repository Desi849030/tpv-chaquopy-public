package com.universidad.tpv.tpvultrasmart;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
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
    private Button btnSend, btnDescargarIA;
    private ScrollView scrollView;
    private ProgressBar progressBar;
    private LinearLayout layoutChat;
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
        btnDescargarIA = findViewById(R.id.btnDescargarIA);
        scrollView = findViewById(R.id.scrollView);
        progressBar = findViewById(R.id.progressBar);
        layoutChat = findViewById(R.id.layoutChat);

        File modeloFile = new File(getFilesDir(), "qwen-coder.gguf");
        
        // Si el modelo ya existe, cambiamos el botón a "Activar"
        if (modeloFile.exists()) {
            btnDescargarIA.setText("Activar Asistente IA");
        }

        txtChat.setText("Bienvenido.\n\nEsta aplicación incluye un Asistente IA Agentic offline.\n\nPresiona el botón para descargarlo (1.2 GB) y activarlo.");

        btnDescargarIA.setOnClickListener(v -> {
            btnDescargarIA.setEnabled(false);
            btnDescargarIA.setText("Procesando...");
            
            if (modeloFile.exists()) {
                // Si ya está descargado, solo carga en RAM
                txtChat.append("\n\nCargando IA en RAM (10 segundos)...\n");
                cargarIA(modeloFile);
            } else {
                // Si no existe, descarga y luego carga
                txtChat.append("\n\nIniciando descarga...\n");
                progressBar.setVisibility(View.VISIBLE);
                descargarYcargarIA(modeloFile);
            }
        });

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

    private void descargarYcargarIA(File modeloFile) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
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
                        progressBar.setVisibility(View.GONE);
                        txtChat.append("Descarga completada.\n");
                        txtChat.append("Cargando IA en RAM...\n");
                    });
                    
                    cargarIA(modeloFile);
                    
                } catch (final Exception e) {
                    runOnUiThread(() -> {
                        txtChat.append("Error descarga: " + e.getMessage() + "\n");
                        btnDescargarIA.setEnabled(true);
                        btnDescargarIA.setText("Reintentar Descarga");
                    });
                }
            }
        }).start();
    }

    private void cargarIA(File modeloFile) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    Python py = Python.getInstance();
                    PyObject module = py.getModule("agente_apk");
                    PyObject result = module.callAttr("inicializar_ia", modeloFile.getAbsolutePath());
                    iaLista = true;
                    
                    runOnUiThread(() -> {
                        txtChat.append(result.toString() + "\n\n¡IA lista! Puedes escribir tu mensaje:\n");
                        btnDescargarIA.setVisibility(View.GONE);
                        layoutChat.setVisibility(View.VISIBLE);
                        scrollView.post(() -> scrollView.fullScroll(ScrollView.FOCUS_DOWN));
                    });
                } catch (final Exception e) {
                    runOnUiThread(() -> {
                        txtChat.append("Error activando IA: " + e.getMessage() + "\n");
                        btnDescargarIA.setEnabled(true);
                        btnDescargarIA.setText("Reintentar Activación");
                    });
                }
            }
        }).start();
    }
}
