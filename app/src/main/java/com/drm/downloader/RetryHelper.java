package com.drm.downloader;

import android.util.Log;

public class RetryHelper {

    public interface RetryTask<T> {
        T run() throws Exception;
    }

    /**
     * Executes a task with automatic retries and exponential backoff delay.
     */
    public static <T> T executeWithRetry(int maxAttempts, long initialDelayMillis, RetryTask<T> task) throws Exception {
        int attempts = 0;
        long currentDelay = initialDelayMillis;

        while (true) {
            try {
                attempts++;
                return task.run(); 
            } catch (Exception e) {
                if (attempts >= maxAttempts) {
                    Log.e("RetryHelper", "Task failed permanently after " + maxAttempts + " attempts.", e);
                    throw e; 
                }

                Log.w("RetryHelper", "Attempt " + attempts + " failed. Retrying in " + currentDelay + "ms...", e);
                
                try {
                    Thread.sleep(currentDelay);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw ie;
                }

                currentDelay *= 2;
            }
        }
    }
}
