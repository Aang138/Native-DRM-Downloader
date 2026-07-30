package com.drm.downloader;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.media.MediaScannerConnection;

import java.io.File;
import java.io.FileInputStream;
import java.io.OutputStream;
import java.io.IOException;

public class ExportHelper {

    public static void exportVideoToPublicStorage(Context context, File sourceFile, String displayName) throws IOException {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ContentResolver resolver = context.getContentResolver();
            ContentValues contentValues = new ContentValues();
            contentValues.put(MediaStore.MediaColumns.DISPLAY_NAME, displayName);
            contentValues.put(MediaStore.MediaColumns.MIME_TYPE, "video/mp4");
            contentValues.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/NativeDRMDownloader");

            Uri uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, contentValues);
            if (uri != null) {
                try (OutputStream out = resolver.openOutputStream(uri);
                     FileInputStream in = new FileInputStream(sourceFile)) {
                    byte[] buffer = new byte[8192];
                    int read;
                    while ((read = in.read(buffer)) != -1) {
                        out.write(buffer, 0, read);
                    }
                }
            }
        } else {
            File downloadsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
            File appDir = new File(downloadsDir, "NativeDRMDownloader");
            if (!appDir.exists()) {
                appDir.mkdirs();
            }
            File destinationFile = new File(appDir, displayName);
            
            try (FileInputStream in = new FileInputStream(sourceFile);
                 OutputStream out = new java.io.FileOutputStream(destinationFile)) {
                byte[] buffer = new byte[8192];
                int read;
                while ((read = in.read(buffer)) != -1) {
                    out.write(buffer, 0, read);
                }
            }
            
            MediaScannerConnection.scanFile(context,
                    new String[]{destinationFile.getAbsolutePath()},
                    null, null);
        }
    }
}
