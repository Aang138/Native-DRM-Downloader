import os
import time
import subprocess
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

def download_selected_stream(url, format_id, manual_key, app_files_dir, callback=None):
    download_path = "/storage/emulated/0/Download/DRM_Downloads"
    os.makedirs(download_path, exist_ok=True)
    
    mp4decrypt_bin = os.path.join(app_files_dir, "mp4decrypt")
    ffmpeg_bin = os.path.join(app_files_dir, "ffmpeg")
    
    if os.path.exists(ffmpeg_bin):
        try: os.chmod(ffmpeg_bin, 0o755)
        except Exception: pass
    if os.path.exists(mp4decrypt_bin):
        try: os.chmod(mp4decrypt_bin, 0o755)
        except Exception: pass

    def my_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', '0 KB/s').strip()
            eta = d.get('_eta_str', 'Unknown').strip()
            if callback:
                try: callback.onProgress(f"{p} | {speed} | ETA: {eta}")
                except Exception: pass

    if callback:
        callback.onProgress("Downloading streams...")

    if format_id != "best":
        target_format = f"{format_id}+bestaudio/best"
    else:
        target_format = "best"

    unique_id = int(time.time())
    enc_output = os.path.join(download_path, f'enc_{unique_id}_%(format_id)s.%(ext)s')

    ydl_opts = {
        'format': target_format,
        'allow_unplayable_formats': True,
        'outtmpl': enc_output,
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
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
    except Exception as e:
        return f"Download failed: {str(e)}"

    # If manual key is provided (Format: KID:KEY), decrypt it!
    if manual_key and ":" in manual_key and os.path.exists(mp4decrypt_bin):
        if callback: callback.onProgress("Decrypting with mp4decrypt...")
        decrypted_file = downloaded_file.replace("enc_", "dec_")
        final_output = os.path.join(download_path, f"playable_{unique_id}.mp4")
        try:
            subprocess.run([mp4decrypt_bin, "--key", manual_key.strip(), downloaded_file, decrypted_file], check=True)
            subprocess.run([ffmpeg_bin, "-i", decrypted_file, "-c", "copy", final_output], check=True)
            
            if os.path.exists(downloaded_file): os.remove(downloaded_file)
            if os.path.exists(decrypted_file): os.remove(decrypted_file)
            return f"Successfully decrypted, merged & saved!"
        except Exception as e:
            return f"Decryption failed: {str(e)}"

    return f"Saved successfully to -> Download/DRM_Downloads"
