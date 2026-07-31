import os
import json
import requests
import yt_dlp

KEY_API_ENDPOINT = "https://your-key-grabber-api.com/get-keys?url="  # Replace with your key API endpoint

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
                
                if vcodec != 'none' and acodec != 'none':
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
        callback.onProgress("Fetching decryption keys from API...")

    # 1. Automatically fetch keys from the remote key API
    key_id, key_hex = "", ""
    try:
        response = requests.get(KEY_API_ENDPOINT + url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            key_id = data.get("key_id", "")
            key_hex = data.get("key", "")
    except Exception as e:
        pass  # Fallback if unencrypted or API unreachable

    if callback:
        callback.onProgress("Downloading encrypted stream...")

    # 2. Download encrypted stream via yt-dlp
    ydl_opts = {
        'format': format_id,
        'allow_unplayable_formats': True,
        'outtmpl': os.path.join(download_path, 'enc_%(id)s.%(ext)s'),
        'progress_hooks': [my_hook],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
    }
    
    downloaded_file = ""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
    except Exception as e:
        return f"Download failed: {str(e)}"

    # 3. If keys were retrieved and binaries exist, decrypt and stitch
    if key_id and key_hex and os.path.exists(mp4decrypt_bin) and os.path.exists(ffmpeg_bin):
        if callback:
            callback.onProgress("Decrypting and stitching media...")
            
        decrypted_file = downloaded_file.replace("enc_", "dec_")
        final_output = downloaded_file.replace("enc_", "").replace(".mp4", "_playable.mp4")
        
        try:
            # Decrypt with mp4decrypt
            subprocess.run([mp4decrypt_bin, "--key", f"{key_id}:{key_hex}", downloaded_file, decrypted_file], check=True)
            
            # Remux / stitch into final playable format with ffmpeg
            subprocess.run([ffmpeg_bin, "-i", decrypted_file, "-c", "copy", final_output], check=True)
            
            # Cleanup temporary raw files
            if os.path.exists(downloaded_file): os.remove(downloaded_file)
            if os.path.exists(decrypted_file): os.remove(decrypted_file)
            
            return f"Successfully decrypted & saved to -> Download/DRM_Downloads"
        except Exception as e:
            return f"Decryption/Stitching failed: {str(e)}"
            
    return f"Saved to Download/DRM_Downloads (Raw)"
