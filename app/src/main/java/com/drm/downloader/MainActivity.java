package com.drm.downloader;

import android.os.Bundle;
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
import java.io.FileOutputStream;
import java.io.InputStream;
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

        // Extract native binaries from assets on first launch
        extractAssetBinaries();

        new Thread(() -> {
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(MainActivity.this));
                    runOnUiThread(() -> statusText.setText("Ready - System Online"));
                }
            } catch (Exception e) {
                runOnUiThread(() -> statusText.setText("Python Init Failed"));
            }
        }).start();

        btnDownload.setOnClickListener(v -> {
            String url = urlInput.getText().toString().trim();
            if (url.isEmpty()) {
                Toast.makeText(MainActivity.this, "Please enter a stream URL", Toast.LENGTH_SHORT).show();
                return;
            }

            statusText.setText("Analyzing stream...");
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
                        showResolutionSelector(url, optionsArray);
                    });
                } catch (Exception e) {
                    runOnUiThread(() -> {
                        btnDownload.setEnabled(true);
                        statusText.setText("Error occurred");
                        Toast.makeText(MainActivity.this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                    });
                }
            }).start();
        });
    }

    private void extractAssetBinaries() {
        String[] binaries = {"ffmpeg", "mp4decrypt"};
        File filesDir = getFilesDir();
        for (String binName : binaries) {
            File outFile = new File(filesDir, binName);
            if (!outFile.exists()) {
                try (InputStream in = getAssets().open(binName);
                     FileOutputStream out = new FileOutputStream(outFile)) {
                    byte[] buffer = new byte[1024];
                    int read;
                    while ((read = in.read(buffer)) != -1) {
                        out.write(buffer, 0, read);
                    }
                    outFile.setExecutable(true, false);
                } catch (Exception e) {
                    // Asset might be missing or handled elsewhere
                }
            } else {
                outFile.setExecutable(true, false);
            }
        }
    }

    private void showResolutionSelector(String url, String[] options) {
        AlertDialog.Builder builder = new AlertDialog.Builder(MainActivity.this);
        builder.setTitle("Select Quality & Size");
        builder.setItems(options, (dialog, which) -> {
            String selectedOption = options[which];
            if (selectedOption.contains("ID:")) {
                selectedFormatId = selectedOption.substring(selectedOption.indexOf("ID:") + 3);
            }
            
            statusText.setText("Checking encryption status...");
            new Thread(() -> {
                try {
                    Python py = Python.getInstance();
                    PyObject module = py.getModule("drm_manager");
                    PyObject isEncryptedObj = module.callAttr("is_encrypted_stream", url);
                    boolean isEncrypted = isEncryptedObj != null && isEncryptedObj.toBoolean();

                    runOnUiThread(() -> {
                        if (isEncrypted) {
                            statusText.setText("Encrypted stream detected");
                            showKeyInputDialog(url, selectedFormatId);
                        } else {
                            statusText.setText("Unencrypted stream");
                            startDownloadProcess(url, selectedFormatId, "");
                        }
                    });
                } catch (Exception e) {
                    runOnUiThread(() -> startDownloadProcess(url, selectedFormatId, ""));
                }
            }).start();
        });
        builder.setNegativeButton("Cancel", (dialog, which) -> statusText.setText("Ready"));
        builder.show();
    }

    private void showKeyInputDialog(String url, String formatId) {
        AlertDialog.Builder builder = new AlertDialog.Builder(MainActivity.this);
        builder.setTitle("Enter DRM Key");
        builder.setMessage("This stream is encrypted. Paste key as: KID:KEY (or multiple comma-separated pairs)");

        final EditText input = new EditText(MainActivity.this);
        input.setHint("e.g., kid1:key1,kid2:key2");
        builder.setView(input);

        builder.setPositiveButton("Download", (dialog, which) -> {
            String manualKey = input.getText().toString().trim();
            startDownloadProcess(url, formatId, manualKey);
        });
        builder.setNegativeButton("Cancel", (dialog, which) -> statusText.setText("Ready"));
        builder.show();
    }

    private void startDownloadProcess(String url, String formatId, String manualKey) {
        statusText.setText("Downloading & processing...");
        btnDownload.setEnabled(false);

        class ProgressCallback {
            public void onProgress(String msg) {
                runOnUiThread(() -> speedText.setText(msg));
            }
        }

        String filesDir = getFilesDir().getAbsolutePath();

        new Thread(() -> {
            try {
                Python py = Python.getInstance();
                PyObject module = py.getModule("drm_manager");
                
                ProgressCallback callback = new ProgressCallback();
                PyObject result = module.callAttr("download_selected_stream", url, formatId, manualKey, filesDir, callback);
                String msg = result != null ? result.toString() : "Completed.";

                runOnUiThread(() -> {
                    btnDownload.setEnabled(true);
                    statusText.setText("Done");
                    speedText.setText("Saved in Download/DRM_Downloads");
                    Toast.makeText(MainActivity.this, msg, Toast.LENGTH_LONG).show();
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    btnDownload.setEnabled(true);
                    statusText.setText("Failed");
                    Toast.makeText(MainActivity.this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                });
            }
        }).start();
    }
}
