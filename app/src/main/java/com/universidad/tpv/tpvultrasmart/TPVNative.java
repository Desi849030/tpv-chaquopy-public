package com.universidad.tpv.tpvultrasmart;

import android.util.Log;
import android.webkit.JavascriptInterface;

public class TPVNative {
    private static final String TAG = "TPVNative";
    private MainActivity activity;

    public TPVNative(MainActivity activity) {
        this.activity = activity;
    }

    @JavascriptInterface
    public void authenticate(String title, String subtitle, String desc) {
        Log.d(TAG, "Biometric auth: " + title);
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                activity.showBiometricPrompt(title, subtitle, desc);
            }
        });
    }

    @JavascriptInterface
    public boolean isAvailable() {
        return activity.checkBiometricAvailable();
    }
}
