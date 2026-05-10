package com.tpv.pos;

import android.annotation.SuppressLint;
import android.graphics.Bitmap;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.KeyEvent;
import android.view.View;
import android.webkit.ConsoleMessage;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.ProgressBar;

/**
 * WebViewManager — Configura y gestiona el WebView principal.
 * Aisla toda la configuracion de JavaScript, cookies, zoom,
 * y callbacks del ciclo de vida del navegador embebido.
 */
public class WebViewManager {
    private static final String TAG = "TPV.WebView";
    private WebView webView;
    private ProgressBar progressBar;
    private Handler mainHandler = new Handler(Looper.getMainLooper());
    private OnPageLoadListener pageLoadListener;

    public interface OnPageLoadListener {
        void onPageStarted(String url);
        void onPageFinished(String url);
        void onPageError(String url, int errorCode);
    }

    public WebViewManager() {}

    /**
     * Inicializa el WebView con configuracion segura y moderna.
     */
    @SuppressLint("SetJavaScriptEnabled")
    public void setupWebView(WebView wv, ProgressBar pb) {
        this.webView = wv;
        this.progressBar = pb;
        if (wv == null) return;

        WebSettings settings = wv.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setSupportZoom(false);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setUserAgentString(settings.getUserAgentString() + " TPV-UltraSmart/2.3");

        wv.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                showProgress();
                if (pageLoadListener != null) pageLoadListener.onPageStarted(url);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                hideProgress();
                if (pageLoadListener != null) pageLoadListener.onPageFinished(url);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request,
                    android.webkit.WebResourceError error) {
                if (pageLoadListener != null) {
                    pageLoadListener.onPageError(request.getUrl().toString(), error.getErrorCode());
                }
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();
                if (url.startsWith("http://127.0.0.1") || url.startsWith("http://localhost")) {
                    return false;
                }
                return true;
            }
        });

        wv.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage msg) {
                if (msg.messageLevel() == ConsoleMessage.MessageLevel.ERROR) {
                    Log.w(TAG, "JS: " + msg.message());
                }
                return true;
            }
        });
    }

    /**
     * Carga la URL principal del servidor local.
     */
    public void loadServerUrl(int port) {
        if (webView != null && port > 0) {
            String url = "http://127.0.0.1:" + port;
            Log.i(TAG, "Cargando: " + url);
            webView.loadUrl(url);
        }
    }

    /**
     * Ejecuta JavaScript en el WebView de forma segura.
     */
    public void executeJs(String script) {
        if (webView != null) {
            mainHandler.post(() -> {
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.KITKAT) {
                    webView.evaluateJavascript(script, null);
                } else {
                    webView.loadUrl("javascript:" + script);
                }
            });
        }
    }

    /**
     * Maneja el boton Back para navegacion historial.
     */
    public boolean handleBackPress() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return false;
    }

    /**
     * Libera recursos del WebView.
     */
    public void destroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.setWebViewClient(null);
            webView.setWebChromeClient(null);
            webView.loadDataWithBaseURL(null, "", "text/html", "utf-8", null);
            webView.clearHistory();
            webView.destroy();
            webView = null;
        }
    }

    public void setOnPageLoadListener(OnPageLoadListener listener) {
        this.pageLoadListener = listener;
    }

    private void showProgress() {
        if (progressBar != null) progressBar.setVisibility(View.VISIBLE);
    }

    private void hideProgress() {
        if (progressBar != null) progressBar.setVisibility(View.GONE);
    }

    public WebView getWebView() { return webView; }
}
