package com.universidad.tpv.tpvultrasmart;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.ProgressBar;
import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends Activity {

    private ListView listViewChat;
    private EditText txtInput;
    private Button btnSend, btnDescargarIA;
    private ProgressBar progressBar;
    private LinearLayout layoutChat;
    private ChatAdapter chatAdapter;
    private boolean iaLista = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // 1. Python se inicializa aquí (rápido y seguro, no congela)
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        listViewChat = findViewById(R.id.listViewChat);
        txtInput = findViewById(R.id.txtInput);
        btnSend = findViewById(R.id.btnSend);
        btnDescargarIA = findViewById(R.id.btnDescargarIA);
        progressBar = findViewById(R.id.progressBar);
        layoutChat = findViewById(R.id.layoutChat);

        chatAdapter = new ChatAdapter(this);
        listViewChat.setAdapter(chatAdapter);

        File modeloFile = new File(getFilesDir(), "qwen-coder.gguf");
        
        if (modeloFile.exists()) {
            btnDescargarIA.setText("Activar Asistente IA");
        }

        chatAdapter.addMessage("Bienvenido a TPV Ultra Smart.", false);
        chatAdapter.addMessage("Esta app incluye un Asistente IA offline. Presiona el botón para comenzar.", false);

        btnDescargarIA.setOnClickListener(v -> {
            btnDescargarIA.setEnabled(false);
            btnDescargarIA.setText("Iniciando...");
            
            if (modeloFile.exists()) {
                chatAdapter.addMessage("Cargando IA en RAM...", false);
                cargarIA(modeloFile);
            } else {
                chatAdapter.addMessage("Iniciando descarga del modelo...", false);
                progressBar.setVisibility(View.VISIBLE);
                progressBar.setIndeterminate(true); // Evita crash si el servidor no da el tamaño
                descargarYcargarIA(modeloFile);
            }
        });

        btnSend.setOnClickListener(v -> {
            String pregunta = txtInput.getText().toString();
            if (!pregunta.isEmpty() && iaLista) {
                chatAdapter.addMessage(pregunta, true);
                txtInput.setText("");
                chatAdapter.addMessage("Pensando...", false);
                
                new Thread(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            Python py = Python.getInstance();
                            PyObject module = py.getModule("agente_apk");
                            PyObject respuesta = module.callAttr("procesar_pregunta", pregunta);
                            final String respText = respuesta.toString();
                            
                            runOnUiThread(() -> chatAdapter.replaceLastMessage(respText));
                        } catch (final Exception e) {
                            runOnUiThread(() -> chatAdapter.replaceLastMessage("Error: " + e.getMessage()));
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
                    if (fileLength > 0) {
                        runOnUiThread(() -> progressBar.setIndeterminate(false));
                    }
                    
                    InputStream input = connection.getInputStream();
                    FileOutputStream output = new FileOutputStream(modeloFile);
                    
                    byte data[] = new byte[8192];
                    long total = 0;
                    int count;
                    
                    while ((count = input.read(data)) != -1) {
                        total += count;
                        if (fileLength > 0) {
                            final int progress = (int) (total * 100 / fileLength);
                            runOnUiThread(() -> progressBar.setProgress(progress));
                        }
                        output.write(data, 0, count);
                    }
                    
                    output.flush();
                    output.close();
                    input.close();
                    
                    runOnUiThread(() -> {
                        progressBar.setVisibility(View.GONE);
                        chatAdapter.addMessage("Descarga completada. Cargando en RAM...", false);
                    });
                    
                    cargarIA(modeloFile);
                    
                } catch (final Exception e) {
                    runOnUiThread(() -> {
                        chatAdapter.addMessage("Error descarga: " + e.getMessage(), false);
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
                        chatAdapter.addMessage(result.toString(), false);
                        chatAdapter.addMessage("¡Hola! Soy tu asistente. ¿En qué puedo ayudarte hoy?", false);
                        btnDescargarIA.setVisibility(View.GONE);
                        layoutChat.setVisibility(View.VISIBLE);
                    });
                } catch (final Exception e) {
                    runOnUiThread(() -> {
                        chatAdapter.addMessage("Error activando IA: " + e.getMessage(), false);
                        btnDescargarIA.setEnabled(true);
                        btnDescargarIA.setText("Reintentar Activación");
                    });
                }
            }
        }).start();
    }
}
