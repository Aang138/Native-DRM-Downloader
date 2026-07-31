package com.drm.downloader;

import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import java.io.File;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    private EditText urlInput;
    private Button btnDownload;
    private TextView statusText, speedText;
    private String selectedFormatId = "best";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        urlInput = findViewById(R.id.urlInput);
        btnDownload = findViewById(R.id.btnDownload);
        statusText = findViewById(R.id.statusText);
        speedText = findViewById(R.id.speedText);

        new Thread(() -> {
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(MainActivity.this));
                    Log.i("MainActivity", "Python initialized successfully.");
                    runOnUiThread(() -> statusText.setText("Ready - System Online"));
                }
            } catch (Exception e) {
                Log.e("MainActivity", "Failed to initialize Python runtime", e);
                runOnUiThread(() -> statusText.setText("Python Init Failed"));
            }
        }).start();

        btnDownload.setOnClickListener(v -> {
            String url = urlInput.getText().toString().trim();
            if (url.isEmpty()) {
                Toast.makeText(MainActivity.this, "Please enter a valid stream URL", Toast.LENGTH_SHORT).show();
                return;
            }

            statusText.setText("Analyzing stream & file sizes...");
            speedText.setText("Parsing...");
            btnDownload.setEnabled(false);

            new Thread(() -> {
                try {
                    Python py = Python.getInstance();
                    PyObject module = py.getModule("drm_manager");
                    PyObject resultList = module.callAttr("get_stream_options", url);
                    
                    List<PyObject> pyList = resultList.asList();
                    String[] optionsArray = new String[pyList.size()];
                    for (int i = 0; i < pyList.size(); i++) {
                        optionsArray[i] = pyList.get(i).toString();
                    }

                    runOnUiThread(() -> {
                        btnDownload.setEnabled(true);
                        statusText.setText("Select resolution");
                        speedText.setText("Idle");
                        showResolutionSelector(url, optionsArray);
                    });

                } catch (Exception e) {
                    Log.e("MainActivity", "Stream extraction failed", e);
                    runOnUiThread(() -> {
                        btnDownload.setEnabled(true);
                        statusText.setText("Error occurred");
                        speedText.setText("Failed");
                        Toast.makeText(MainActivity.this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                    });
                }
            }).start();
        });
    }

    private void showResolutionSelector(String url, String[] options) {
        AlertDialog.Builder builder = new AlertDialog.Builder(MainActivity.this);
        builder.setTitle("Select Quality & File Size");
        
        builder.setItems(options, (dialog, which) -> {
            String selectedOption = options[which];
            if (selectedOption.contains("ID:")) {
                selectedFormatId = selectedOption.substring(selectedOption.indexOf("ID:") + 3);
            }
            
            Toast.makeText(MainActivity.this, "Selected: " + selectedOption, Toast.LENGTH_SHORT).show();
            startDownloadProcess(url, selectedFormatId);
        });
        
        builder.setNegativeButton("Cancel", (dialog, which) -> {
            statusText.setText("Ready");
            speedText.setText("Idle");
        });
        builder.show();
    }

    private void startDownloadProcess(String url, String formatId) {
        statusText.setText("Downloading & decrypting fragments...");
        speedText.setText("Connecting...");
        btnDownload.setEnabled(false);

        class ProgressCallback {
            public void onProgress(String progressMessage) {
                runOnUiThread(() -> speedText.setText(progressMessage));
            }
        }

        String filesDir = getFilesDir().getAbsolutePath();

        new Thread(() -> {
            try {
                Python py = Python.getInstance();
                PyObject module = py.getModule("drm_manager");
                
                ProgressCallback callback = new ProgressCallback();
                PyObject result = module.callAttr("download_selected_stream", url, formatId, filesDir, callback);
                String msg = result != null ? result.toString() : "Download completed.";

                runOnUiThread(() -> {
                    btnDownload.setEnabled(true);
                    statusText.setText("Download Complete");
                    speedText.setText("Saved in Download/DRM_Downloads");
                    Toast.makeText(MainActivity.this, msg, Toast.LENGTH_LONG).show();
                });

            } catch (Exception e) {
                Log.e("MainActivity", "Download failed", e);
                runOnUiThread(() -> {
                    btnDownload.setEnabled(true);
                    statusText.setText("Download Failed");
                    speedText.setText("Error");
                    Toast.makeText(MainActivity.this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                });
            }
        }).start();
    }
}
