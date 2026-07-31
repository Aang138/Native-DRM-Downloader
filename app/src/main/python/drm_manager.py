import os
import yt_dlp
from curl_cffi import requests

def get_stream_options(url):
    ydl_opts = {
        'extractor_args': {'generic': {'impersonate': 'chrome'}},
        'socket_timeout': 30,
        'quiet': True,
    }
    options = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [info])
            for f in formats:
                format_id = f.get('format_id', 'best')
                ext = f.get('ext', 'mp4')
                resolution = f.get('resolution', f.get('format_note', 'HD'))
                filesize = f.get('filesize', f.get('filesize_approx', 0))
                size_mb = round(filesize / (1024 * 1024), 2) if filesize else "Unknown"
                desc = f"Res: {resolution} | Ext: {ext} | Size: {size_mb}MB | ID:{format_id}"
                options.append(desc)
        if not options:
            options.append("Best Quality Available | ID:best")
    except Exception as e:
        options.append(f"Error parsing stream: {str(e)} | ID:best")
    return options

def download_selected_stream(url, format_id, callback=None):
    download_path = "/storage/emulated/0/Download/DRM_Downloads"
    os.makedirs(download_path, exist_ok=True)
    
    def my_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', '0 KB/s').strip()
            eta = d.get('_eta_str', 'Unknown').strip()
            msg = f"{p} | {speed} | ETA: {eta}"
            if callback:
                try:
                    callback.onProgress(msg)
                except Exception:
                    pass
        elif d['status'] == 'finished':
            if callback:
                try:
                    callback.onProgress("Merging video & audio...")
                except Exception:
                    pass

    ydl_opts = {
        'format': format_id,
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'progress_hooks': [my_hook],
        'extractor_args': {'generic': {'impersonate': 'chrome'}},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return "Saved to Phone Storage -> Download/DRM_Downloads"
    except Exception as e:
        return f"Download failed: {str(e)}"
