package com.universidad.tpv.tpvultrasmart;

import android.app.Application;
import android.content.Context;
import android.os.SystemClock;
import android.util.Log;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainApplication extends Application {
    private static final String TAG = "TPV";
    private static final Object PY_LOCK = new Object();
    private static boolean pythonInitStarted = false;
    private static boolean pythonInitDone = false;
    private static Throwable pythonInitError = null;

    @Override
    public void onCreate() {
        super.onCreate();
        prewarmPython(getApplicationContext());
    }

    public static void prewarmPython(Context context) {
        final Context appContext = context.getApplicationContext();
        synchronized (PY_LOCK) {
            if (pythonInitStarted) {
                return;
            }
            pythonInitStarted = true;
        }
        Thread t = new Thread(() -> {
            try {
                startPythonBlocking(appContext);
            } catch (Throwable t1) {
                Log.e(TAG, "Error prewarming Python", t1);
            }
        }, "tpv-python-prewarm");
        t.setDaemon(true);
        t.start();
    }

    public static void awaitPythonReady(Context context, long timeoutMs) {
        prewarmPython(context);
        long deadline = SystemClock.uptimeMillis() + Math.max(0, timeoutMs);
        synchronized (PY_LOCK) {
            while (!pythonInitDone) {
                long remaining = deadline - SystemClock.uptimeMillis();
                if (remaining <= 0) {
                    break;
                }
                try {
                    PY_LOCK.wait(remaining);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
        if (!pythonInitDone || !Python.isStarted()) {
            startPythonBlocking(context.getApplicationContext());
        }
        if (pythonInitError != null) {
            throw new RuntimeException("No se pudo inicializar Python", pythonInitError);
        }
    }

    private static void startPythonBlocking(Context context) {
        synchronized (PY_LOCK) {
            if (pythonInitDone && pythonInitError == null && Python.isStarted()) {
                return;
            }
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(context));
                }
                pythonInitError = null;
            } catch (Throwable t) {
                pythonInitError = t;
                throw t;
            } finally {
                pythonInitDone = true;
                PY_LOCK.notifyAll();
            }
        }
    }
}
