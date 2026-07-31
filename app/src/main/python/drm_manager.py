import os
import time
import requests
import subprocess
import yt_dlp

def is_encrypted_stream(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10)
        text = res.text.lower()
        if 'contentprotection' in text or 'pssh' in text:
            return True
    except Exception:
        pass
    return False

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
    
    if os.path.exists(ffmpeg_bin): os.chmod(ffmpeg_bin, 0o755)
    if os.path.exists(mp4decrypt_bin): os.chmod(mp4decrypt_bin, 0o755)

    def my_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', '0 KB/s').strip()
            eta = d.get('_eta_str', 'Unknown').strip()
            if callback:
                try: callback.onProgress(f"{p} | {speed} | ETA: {eta}")
                except Exception: pass
        elif d['status'] == 'finished':
            if callback:
                try: callback.onProgress("Processing files...")
                except Exception: pass

    if format_id != "best":
        target_format = f"{format_id}+bestaudio/best"
    else:
        target_format = "best"

    unique_id = int(time.time())
    # Use a clean prefix to easily locate downloaded components
    raw_template = os.path.join(download_path, f'temp_{unique_id}_%(format_id)s.%(ext)s')

    if callback: callback.onProgress("Downloading streams...")
    ydl_opts = {
        'format': target_format,
        'allow_unplayable_formats': True,
        'outtmpl': raw_template,
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

    # Gather all files created in this session
    files = [os.path.join(download_path, f) for f in os.listdir(download_path) if f.startswith(f"temp_{unique_id}")]
    
    if not files:
        return f"Download failed: No files found."

    # Identify video and audio tracks reliably
    video_file = next((f for f in files if f.endswith(('.mp4', '.mkv', '.webm')) and 'audio' not in f and 'm4a' not in f), None)
    audio_file = next((f for f in files if f.endswith(('.m4a', '.aac', '.opus')) or 'audio' in f), None)
    
    if not video_file and files:
        video_file = files[0]
    if not audio_file and len(files) > 1:
        audio_file = files[1]

    final_output = os.path.join(download_path, f"playable_{unique_id}.mp4")

    # STEP 1: Decrypt if manual key is provided (Encrypted stream)
    if manual_key and ":" in manual_key and os.path.exists(mp4decrypt_bin):
        if callback: callback.onProgress("Decrypting tracks with mp4decrypt...")
        dec_video = video_file.replace("temp_", "dec_") if video_file else None
        dec_audio = audio_file.replace("temp_", "dec_") if audio_file else None
        try:
            if video_file:
                subprocess.run([mp4decrypt_bin, "--key", manual_key.strip(), video_file, dec_video], check=True)
            if audio_file:
                subprocess.run([mp4decrypt_bin, "--key", manual_key.strip(), audio_file, dec_audio], check=True)
            
            if dec_video and os.path.exists(dec_video): video_file = dec_video
            if dec_audio and os.path.exists(dec_audio): audio_file = dec_audio
        except Exception as e:
            return f"Decryption failed: {str(e)}"

    # STEP 2: Explicit Python-side FFmpeg Merge (Guaranteed combination)
    if callback: callback.onProgress("Merging video & audio with ffmpeg...")
    try:
        if video_file and audio_file and os.path.exists(ffmpeg_bin):
            cmd = [ffmpeg_bin, "-y", "-i", video_file, "-i", audio_file, "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", final_output]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                # Fallback if stream map mismatch occurs
                cmd_fallback = [ffmpeg_bin, "-y", "-i", video_file, "-c", "copy", final_output]
                subprocess.run(cmd_fallback, check=True)
        elif video_file:
            os.rename(video_file, final_output)

        # Cleanup raw temporary component files
        for f in files:
            if os.path.exists(f): os.remove(f)
        if 'dec_video' in locals() and dec_video and os.path.exists(dec_video): os.remove(dec_video)
        if 'dec_audio' in locals() and dec_audio and os.path.exists(dec_audio): os.remove(dec_audio)

        return f"Successfully merged & saved!"
    except Exception as e:
        return f"Merging failed: {str(e)}"
