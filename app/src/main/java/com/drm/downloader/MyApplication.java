package com.drm.downloader;

import android.app.Application;
import android.util.Log;
import com.yausername.youtubedl.YoutubeDL;
import com.yausername.youtubedl.YoutubeDLException;
import com.yausername.ffmpeg.FFmpeg;
import com.aria2c.android.Aria2c;
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
            YoutubeDL.getInstance().init(this);
            FFmpeg.getInstance().init(this);
            Aria2c.getInstance().init(this);
            Log.d("MyApplication", "All tools and Python runtime initialized successfully.");
        } catch (YoutubeDLException e) {
            Log.e("MyApplication", "Failed to initialize tools", e);
        }
    }
}
