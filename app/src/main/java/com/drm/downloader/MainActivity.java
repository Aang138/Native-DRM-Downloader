package com.drm.downloader;

import android.os.Bundle;
import android.util.Log;
import androidx.appcompat.app.AppCompatActivity;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize Python in a background thread to prevent app freezing on startup
        new Thread(() -> {
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(MainActivity.this));
                    Log.i("MainActivity", "Python initialized successfully.");
                }
            } catch (Exception e) {
                Log.e("MainActivity", "Failed to initialize Python runtime", e);
            }
        }).start();
    }
}
