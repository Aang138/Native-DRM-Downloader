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

def download_selected_stream(url, format_id, manual_key, callback=None):
    download_path = "/storage/emulated/0/Download/DRM_Downloads"
    os.makedirs(download_path, exist_ok=True)

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

    # Download both video format and best audio format separately so both tracks are saved
    if format_id != "best":
        target_format = f"{format_id}+bestaudio/best"
    else:
        target_format = "bestvideo+bestaudio/best"

    unique_id = int(time.time())
    raw_template = os.path.join(download_path, f'dl_{unique_id}_%(format_id)s.%(ext)s')

    if callback: callback.onProgress(5, "Downloading video and audio tracks...")

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

    session_files = [os.path.join(download_path, f) for f in os.listdir(download_path) if f.startswith(f"dl_{unique_id}")]

    if not session_files:
        return f"Download failed: No files generated."

    video_file = next((f for f in session_files if f.endswith(('.mp4', '.mkv', '.webm')) and 'm4a' not in f and 'opus' not in f and 'aac' not in f), None)
    audio_file = next((f for f in session_files if f.endswith(('.m4a', '.aac', '.opus'))), None)

    if not video_file and session_files:
        video_file = session_files[0]
    if not audio_file:
        audio_file = next((f for f in session_files if f != video_file), None)

    # Optional optional local decryption using mp4decrypt if binary exists in local app folder
    app_files_dir = os.path.dirname(os.path.abspath(__file__))
    mp4decrypt_bin = os.path.join(app_files_dir, "mp4decrypt")

    dec_video = None
    dec_audio = None
    if manual_key and ":" in manual_key and os.path.exists(mp4decrypt_bin):
        if callback: callback.onProgress(85, "Decrypting tracks with mp4decrypt...")
        dec_video = video_file.replace("dl_", "dec_") if video_file else None
        dec_audio = audio_file.replace("dl_", "dec_") if audio_file else None
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
            pass

    if callback: callback.onProgress(100, "Download Complete (Video & Audio saved separately)!")
    return "Successfully downloaded video and audio tracks to Download/DRM_Downloads!"
