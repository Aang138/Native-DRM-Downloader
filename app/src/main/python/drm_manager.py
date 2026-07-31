import os
import time
import yt_dlp

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
                
                if vcodec != 'none':
                    filesize = f.get('filesize', f.get('filesize_approx', 0))
                    size_mb = round(filesize / (1024 * 1024), 2) if filesize else "Unknown"
                    desc = f"Res: {resolution} | Ext: {ext} | Size: {size_mb}MB | ID:{format_id}"
                    options.append(desc)
                    
        if not options:
            options.append("Best Quality Available | ID:best")
    except Exception as e:
        options.append(f"Error parsing stream: {str(e)} | ID:best")
    return options

def download_selected_stream(url, format_id, app_files_dir, callback=None):
    download_path = "/storage/emulated/0/Download/DRM_Downloads"
    os.makedirs(download_path, exist_ok=True)
    
    ffmpeg_bin = os.path.join(app_files_dir, "ffmpeg")
    
    # Grant execution permissions to ffmpeg binary to prevent silent merge failure on Android
    if os.path.exists(ffmpeg_bin):
        try:
            os.chmod(ffmpeg_bin, 0o755)
        except Exception:
            pass

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
                    callback.onProgress("Merging video & audio tracks...")
                except Exception:
                    pass

    if callback:
        callback.onProgress("Initializing download & merge engine...")

    if format_id != "best":
        target_format = f"{format_id}+bestaudio/best"
    else:
        target_format = "best"

    unique_id = int(time.time())
    target_outtmpl = os.path.join(download_path, f'video_{unique_id}_%(title)s.%(ext)s')

    ydl_opts = {
        'format': target_format,
        'allow_unplayable_formats': True,
        'outtmpl': target_outtmpl,
        'progress_hooks': [my_hook],
        'merge_output_format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
    }
    
    if os.path.exists(ffmpeg_bin):
        ydl_opts['ffmpeg_location'] = ffmpeg_bin

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return f"Download failed: {str(e)}"

    return f"Successfully saved and merged to -> Download/DRM_Downloads"
