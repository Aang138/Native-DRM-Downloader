package com.drm.downloader;

import android.os.Bundle;
import android.os.Environment;
import android.util.Log;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.yausername.youtubedl.YoutubeDL;
import com.yausername.youtubedl.YoutubeDLRequest;

import java.io.File;

public class MainActivity extends AppCompatActivity {

    private EditText etVideoUrl, etPssh, etLicenseUrl;
    private Button btnDownload;
    private TextView tvStatus;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        etVideoUrl = findViewById(R.id.etVideoUrl);
        etPssh = findViewById(R.id.etPssh);
        etLicenseUrl = findViewById(R.id.etLicenseUrl);
        btnDownload = findViewById(R.id.btnDownload);
        tvStatus = findViewById(R.id.tvStatus);

        btnDownload.setOnClickListener(v -> {
            String url = etVideoUrl.getText().toString().trim();
            String pssh = etPssh.getText().toString().trim();
            String licenseUrl = etLicenseUrl.getText().toString().trim();

            if (url.isEmpty()) {
                tvStatus.setText("Error: Please enter a video URL");
                return;
            }

            startPipeline(url, pssh, licenseUrl);
        });
    }

    private void startPipeline(String videoUrl, String pssh, String licenseUrl) {
        tvStatus.setText("Status: Processing pipeline...");

        new Thread(() -> {
            try {
                // Step 1: Grab keys via Python (pywidevine) if PSSH is provided
                if (!pssh.isEmpty() && !licenseUrl.isEmpty()) {
                    runOnUiThread(() -> tvStatus.setText("Status: Grabbing DRM keys..."));
                    Python py = Python.getInstance();
                    PyObject pyModule = py.getModule("key_grabber");
                    PyObject keysResult = pyModule.callAttr("fetch_keys", pssh, licenseUrl);
                    Log.d("KeyGrabber", "Result: " + keysResult.toString());
                }

                // Step 2: Download stream using yt-dlp and aria2c
                runOnUiThread(() -> tvStatus.setText("Status: Downloading streams..."));
                File outputDir = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), "DRM-Downloader");
                if (!outputDir.exists()) outputDir.mkdirs();

                YoutubeDLRequest request = new YoutubeDLRequest(videoUrl);
                request.addOption("--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
                request.addOption("--downloader", "aria2c");
                request.addOption("--external-downloader-args", "aria2c:\"-j8 -x8 -s8\"");
                request.addOption("-o", outputDir.getAbsolutePath() + "/output.%(ext)s");

                YoutubeDL.getInstance().execute(request, (progress, etaInSeconds, line) -> {
                    runOnUiThread(() -> tvStatus.setText("Downloading: " + progress + "% | ETA: " + etaInSeconds + "s"));
                });

                runOnUiThread(() -> tvStatus.setText("Status: Download completed successfully!"));

            } catch (Exception e) {
                Log.e("MainActivity", "Pipeline error", e);
                runOnUiThread(() -> tvStatus.setText("Error: " + e.getMessage()));
            }
        }).start();
    }
}
