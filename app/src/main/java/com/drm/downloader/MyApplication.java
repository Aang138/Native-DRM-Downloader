package com.drm.downloader;

import android.app.Application;
import android.util.Log;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MyApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        try {
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(this));
            }
        } catch (Exception e) {
            Log.e("MyApplication", "Python initialization failed", e);
        }
    }
}
