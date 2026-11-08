package com.constantine.mobile;

import android.app.Activity;
import android.net.Uri;
import android.os.Bundle;
import android.view.WindowManager;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public final class GameActivity extends Activity {
    private WebView game;
    private static final String LOCAL_GAME = "file:///android_asset/index.html";

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                             WindowManager.LayoutParams.FLAG_FULLSCREEN);
        game = new WebView(this);
        game.getSettings().setJavaScriptEnabled(true);
        game.getSettings().setAllowFileAccess(false);
        game.getSettings().setAllowContentAccess(false);
        game.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri destination = request.getUrl();
                return !"https".equals(destination.getScheme()) &&
                    !LOCAL_GAME.equals(destination.toString());
            }
        });
        setContentView(game);
        game.loadUrl(LOCAL_GAME);
    }

    @Override public void onBackPressed() {
        if (game.canGoBack()) game.goBack();
        else super.onBackPressed();
    }
}
