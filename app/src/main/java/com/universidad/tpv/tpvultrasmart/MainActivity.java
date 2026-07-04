package com.universidad.tpv.tpvultrasmart;

import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ScrollView;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

public class MainActivity extends AppCompatActivity {

    private TextView txtChat;
    private EditText txtInput;
    private Button btnSend;
    private ScrollView scrollView;
    private boolean iaLista = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        txtChat = findViewById(R.id.txtChat);
        txtInput = findViewById(R.id.txtInput);
        btnSend = findViewById(R.id.btnSend);
        scrollView = findViewById(R.id.scrollView);

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
                        runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                txtChat.append("Copiando modelo de IA (1.2 GB)...\n");
                            }
                        });
                        
                        try (InputStream is = getAssets().open("qwen-coder.gguf");
                             OutputStream os = new FileOutputStream(modeloFile)) {
                            byte[] buffer = new byte[8192];
                            int length;
                            while ((length = is.read(buffer)) > 0) {
                                os.write(buffer, 0, length);
                            }
                        }
                    }
                    
                    PyObject result = module.callAttr("inicializar_ia", modeloFile.getAbsolutePath());
                    iaLista = true;
                    
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            txtChat.append(result.toString() + "\n\nPuedes hablar con la IA:\n");
                            btnSend.setEnabled(true);
                        }
                    });
                } catch (final Exception e) {
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            txtChat.append("Error inicializando: " + e.getMessage() + "\n");
                        }
                    });
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
                        Python py = Python.getInstance();
                        PyObject module = py.getModule("agente_apk");
                        PyObject respuesta = module.callAttr("procesar_pregunta", pregunta);
                        
                        runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                String textoActual = txtChat.getText().toString();
                                txtChat.setText(textoActual.replace("IA: Pensando...\n", "IA: " + respuesta.toString() + "\n"));
                                scrollView.post(() -> scrollView.fullScroll(ScrollView.FOCUS_DOWN));
                            }
                        });
                    }
                }).start();
            }
        });
    }
}
