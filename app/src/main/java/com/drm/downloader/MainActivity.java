package com.drm.downloader;

import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.VideoView;
import android.widget.MediaController;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    private EditText urlInput;
    private Button btnDownload, btnPlay;
    private TextView statusText, speedText;
    private ProgressBar progressBar;
    private VideoView videoView;
    private String selectedFormatId = "best";
    private String lastDownloadedFile = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        urlInput = findViewById(R.id.urlInput);
        btnDownload = findViewById(R.id.btnDownload);
        btnPlay = findViewById(R.id.btnPlay);
        statusText = findViewById(R.id.statusText);
        speedText = findViewById(R.id.speedText);
        progressBar = findViewById(R.id.progressBar);
        videoView = findViewById(R.id.videoView);

        prepareBinaries();

        MediaController mediaController = new MediaController(this);
        mediaController.setAnchorView(videoView);
        videoView.setMediaController(mediaController);

        btnPlay.setOnClickListener(v -> {
            if (!lastDownloadedFile.isEmpty() && new File(lastDownloadedFile).exists()) {
                videoView.setVideoURI(Uri.parse(lastDownloadedFile));
                videoView.start();
                Toast.makeText(this, "Playing video...", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "No downloaded video found yet!", Toast.LENGTH_SHORT).show();
            }
        });

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
            progressBar.setProgress(0);
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

    private void prepareBinaries() {
        File nativeDir = new File(getApplicationInfo().nativeLibraryDir);
        File codeCache = getCodeCacheDir();
        copyAndRename(new File(nativeDir, "libffmpeg.so"), new File(codeCache, "ffmpeg"));
        copyAndRename(new File(nativeDir, "libmp4decrypt.so"), new File(codeCache, "mp4decrypt"));
    }

    private void copyAndRename(File src, File dst) {
        if (!src.exists()) return;
        try (InputStream in = new FileInputStream(src);
             OutputStream out = new FileOutputStream(dst)) {
            byte[] buf = new byte[4096];
            int len;
            while ((len = in.read(buf)) > 0) {
                out.write(buf, 0, len);
            }
            dst.setExecutable(true, false);
        } catch (Exception e) {
            // ignore
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
        builder.setMessage("This stream is encrypted. Paste key as: KID:KEY");

        final EditText input = new EditText(MainActivity.this);
        input.setHint("e.g., kid1:key1");
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
            public void onProgress(int percent, String msg) {
                runOnUiThread(() -> {
                    progressBar.setProgress(percent);
                    speedText.setText(msg);
                });
            }
        }

        String codeCachePath = getCodeCacheDir().getAbsolutePath();

        new Thread(() -> {
            try {
                Python py = Python.getInstance();
                PyObject module = py.getModule("drm_manager");
                
                ProgressCallback callback = new ProgressCallback();
                PyObject result = module.callAttr("download_selected_stream", url, formatId, manualKey, codeCachePath, callback);
                PyObject filePathObj = module.get("last_saved_file");
                if (filePathObj != null) {
                    lastDownloadedFile = filePathObj.toString();
                }
                String msg = result != null ? result.toString() : "Completed.";

                runOnUiThread(() -> {
                    btnDownload.setEnabled(true);
                    if (msg.contains("Successfully")) {
                        statusText.setText("Download Successful!");
                        speedText.setTextColor(0xFF00E676);
                    } else {
                        statusText.setText("Download Failed!");
                        speedText.setTextColor(0xFFFF1744);
                    }
                    Toast.makeText(MainActivity.this, msg, Toast.LENGTH_LONG).show();
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    btnDownload.setEnabled(true);
                    statusText.setText("Download Failed!");
                    speedText.setTextColor(0xFFFF1744);
                    Toast.makeText(MainActivity.this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                });
            }
        }).start();
    }
}
