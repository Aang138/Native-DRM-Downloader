import os
import time
import requests
import subprocess
import yt_dlp

last_saved_file = ""

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

def download_selected_stream(url, format_id, manual_key, code_cache_dir, callback=None):
    global last_saved_file
    download_path = "/storage/emulated/0/Download/DRM_Downloads"
    os.makedirs(download_path, exist_ok=True)

    ffmpeg_bin = os.path.join(code_cache_dir, "ffmpeg")
    mp4decrypt_bin = os.path.join(code_cache_dir, "mp4decrypt")

    def my_hook(d):
        if d['status'] == 'downloading':
            p_str = d.get('_percent_str', '0%').strip().replace('%', '')
            try:
                p_int = int(float(p_str))
            except:
                p_int = 0
            speed = d.get('_speed_str', '0 KB/s').strip()
            eta = d.get('_eta_str', 'Unknown').strip()
            if callback:
                try: callback.onProgress(p_int, f"Downloading: {p_str}% | Speed: {speed} | ETA: {eta}")
                except Exception: pass

    if format_id != "best":
        target_format = f"{format_id}+bestaudio/best"
    else:
        target_format = "best"

    unique_id = int(time.time())
    raw_template = os.path.join(download_path, f'dl_{unique_id}_%(format_id)s.%(ext)s')

    if callback: callback.onProgress(5, "Initializing download...")

    ydl_opts = {
        'format': target_format,
        'allow_unplayable_formats': True,
        'outtmpl': raw_template,
        'progress_hooks': [my_hook],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
    }
    if os.path.exists(ffmpeg_bin):
        ydl_opts['ffmpeg_location'] = code_cache_dir

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return f"Download failed: {str(e)}"

    session_files = [os.path.join(download_path, f) for f in os.listdir(download_path) if f.startswith(f"dl_{unique_id}")]

    if not session_files:
        return f"Download failed: No files generated."

    video_file = next((f for f in session_files if f.endswith(('.mp4', '.mkv', '.webm')) and 'm4a' not in f and 'opus' not in f and 'aac' not in f), None)
    audio_file = next((f for f in session_files if f.endswith(('.m4a', '.aac', '.opus'))), None)

    if not video_file and session_files:
        video_file = session_files[0]
    if not audio_file:
        audio_file = next((f for f in session_files if f != video_file), None)

    final_output = os.path.join(download_path, f"playable_{unique_id}.mp4")
    dec_video = None
    dec_audio = None

    if manual_key and ":" in manual_key and os.path.exists(mp4decrypt_bin):
        if callback: callback.onProgress(85, "Decrypting DRM tracks...")
        dec_video = video_file.replace("dl_", "dec_") if video_file else None
        dec_audio = audio_file.replace("dl_", "dec_") if video_file else None
        key_args = []
        for pair in manual_key.strip().split(","):
            pair = pair.strip()
            if ":" in pair:
                key_args += ["--key", pair]
        try:
            if video_file and os.path.exists(video_file):
                subprocess.run([mp4decrypt_bin] + key_args + [video_file, dec_video], check=True)
                video_file = dec_video
            if audio_file and os.path.exists(audio_file):
                subprocess.run([mp4decrypt_bin] + key_args + [audio_file, dec_audio], check=True)
                audio_file = dec_audio
        except Exception as e:
            return f"Decryption failed: {str(e)}"

    if callback: callback.onProgress(90, "Merging audio and video tracks...")
    try:
        if video_file and audio_file and os.path.exists(ffmpeg_bin) and os.path.exists(video_file) and os.path.exists(audio_file):
            cmd = [ffmpeg_bin, "-y", "-i", video_file, "-i", audio_file,
                   "-map", "0:v:0", "-map", "1:a:0",
                   "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", final_output]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                cmd_reencode = [ffmpeg_bin, "-y", "-i", video_file, "-i", audio_file,
                                 "-map", "0:v:0", "-map", "1:a:0",
                                 "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                                 "-movflags", "+faststart", final_output]
                subprocess.run(cmd_reencode, check=True)
        elif video_file and os.path.exists(video_file):
            os.rename(video_file, final_output)

        for f in session_files:
            if os.path.exists(f): os.remove(f)
        if dec_video and os.path.exists(dec_video): os.remove(dec_video)
        if dec_audio and os.path.exists(dec_audio): os.remove(dec_audio)

        last_saved_file = final_output
        if callback: callback.onProgress(100, "Download Complete!")
        return "Successfully downloaded, merged & saved with audio!"
    except Exception as e:
        return f"Merging failed: {str(e)}"
