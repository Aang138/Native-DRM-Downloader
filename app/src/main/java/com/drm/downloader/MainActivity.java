package com.drm.downloader;

import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {

    private EditText urlInput;
    private Button btnDownload;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        urlInput = findViewById(R.id.urlInput);
        btnDownload = findViewById(R.id.btnDownload);

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

        btnDownload.setOnClickListener(v -> {
            String url = urlInput.getText().toString().trim();
            if (url.isEmpty()) {
                Toast.makeText(MainActivity.this, "Please enter a valid stream URL", Toast.LENGTH_SHORT).show();
                return;
            }

            Toast.makeText(MainActivity.this, "Analyzing stream and fetching options...", Toast.LENGTH_LONG).show();
            btnDownload.setEnabled(false);

            new Thread(() -> {
                try {
                    Python py = Python.getInstance();
                    PyObject module = py.getModule("drm_manager");
                    PyObject result = module.callAttr("get_stream_options", url);
                    
                    String streamDetails = result != null ? result.toString() : "Streams parsed successfully.";

                    runOnUiThread(() -> {
                        btnDownload.setEnabled(true);
                        showStreamOptionsDialog(streamDetails);
                    });

                } catch (Exception e) {
                    Log.e("MainActivity", "Stream extraction failed", e);
                    runOnUiThread(() -> {
                        btnDownload.setEnabled(true);
                        Toast.makeText(MainActivity.this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                    });
                }
            }).start();
        });
    }

    private void showStreamOptionsDialog(String details) {
        new AlertDialog.Builder(MainActivity.this)
            .setTitle("Available Streams & Audio")
            .setMessage(details)
            .setPositiveButton("Start Download", (dialog, which) -> {
                Toast.makeText(MainActivity.this, "Initiating download & decryption...", Toast.LENGTH_SHORT).show();
            })
            .setNegativeButton("Cancel", null)
            .show();
    }
}
