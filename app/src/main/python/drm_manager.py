import os
import subprocess
import requests
import yt_dlp

KEY_API_ENDPOINT = ""

def get_stream_options(url):
    ydl_opts = {
        'allow_unplayable_formats': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
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
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                
                if vcodec != 'none':
                    filesize = f.get('filesize', f.get('filesize_approx', 0))
                    size_mb = round(filesize / (1024 * 1024), 2) if filesize else "Unknown"
                    desc = f"Res: {resolution} | Ext: {ext} | Size: {size_mb}MB | ID:{format_id}"
                    options.append(desc)
                    
        if not options:
            options.append("Best Quality Single File | ID:best")
    except Exception as e:
        options.append(f"Error parsing stream: {str(e)} | ID:best")
    return options

def download_selected_stream(url, format_id, app_files_dir, callback=None):
    download_path = "/storage/emulated/0/Download/DRM_Downloads"
    os.makedirs(download_path, exist_ok=True)
    
    mp4decrypt_bin = os.path.join(app_files_dir, "mp4decrypt")
    ffmpeg_bin = os.path.join(app_files_dir, "ffmpeg")
    
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

    if callback:
        callback.onProgress("Downloading stream...")

    target_outtmpl = os.path.join(download_path, 'downloaded_video.%(ext)s')

    ydl_opts = {
        'format': format_id,
        'allow_unplayable_formats': True,
        'outtmpl': target_outtmpl,
        'progress_hooks': [my_hook],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return f"Download failed: {str(e)}"

    return f"Saved successfully to -> Download/DRM_Downloads"
