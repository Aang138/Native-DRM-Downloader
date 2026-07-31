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
                try: callback.onProgress("Finalizing file...")
                except Exception: pass

    if format_id != "best":
        target_format = f"{format_id}+bestaudio/best"
    else:
        target_format = "best"

    unique_id = int(time.time())
    target_outtmpl = os.path.join(download_path, f'video_{unique_id}_%(title)s.%(ext)s')

    # CASE 1: UNENCRYPTED STREAM (No manual key given) -> Let yt-dlp + ffmpeg handle auto-merging smoothly
    if not manual_key or ":" not in manual_key:
        if callback: callback.onProgress("Downloading & merging stream...")
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
            return f"Successfully downloaded & merged!"
        except Exception as e:
            return f"Download failed: {str(e)}"

    # CASE 2: ENCRYPTED STREAM (Manual key provided) -> Download raw tracks, decrypt, and stitch
    else:
        if callback: callback.onProgress("Downloading encrypted streams...")
        enc_output = os.path.join(download_path, f'raw_{unique_id}_%(format_id)s.%(ext)s')
        ydl_opts = {
            'format': target_format,
            'allow_unplayable_formats': True,
            'outtmpl': enc_output,
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

        downloaded_files = [os.path.join(download_path, f) for f in os.listdir(download_path) if f.startswith(f"raw_{unique_id}")]
        video_file = next((f for f in downloaded_files if "video" in f or format_id in f), None)
        audio_file = next((f for f in downloaded_files if "audio" in f or "f251" in f or "f140" in f or "mp4a" in f), None)
        
        if not video_file:
            return f"Download failed: Video stream not found."

        final_output = os.path.join(download_path, f"playable_{unique_id}.mp4")

        if callback: callback.onProgress("Decrypting tracks with mp4decrypt...")
        dec_video = video_file.replace("raw_", "dec_")
        try:
            subprocess.run([mp4decrypt_bin, "--key", manual_key.strip(), video_file, dec_video], check=True)
        except Exception as e:
            return f"Video decryption failed: {str(e)}"
            
        dec_audio = None
        if audio_file:
            dec_audio = audio_file.replace("raw_", "dec_")
            try:
                subprocess.run([mp4decrypt_bin, "--key", manual_key.strip(), audio_file, dec_audio], check=True)
            except Exception:
                dec_audio = None

        if callback: callback.onProgress("Stitching audio and video with ffmpeg...")
        try:
            if dec_audio and os.path.exists(dec_audio):
                cmd = [ffmpeg_bin, "-i", dec_video, "-i", dec_audio, "-c:v", "copy", "-c:a", "copy", final_output]
            else:
                cmd = [ffmpeg_bin, "-i", dec_video, "-c", "copy", final_output]
                
            subprocess.run(cmd, check=True)
            
            for f in downloaded_files:
                if os.path.exists(f): os.remove(f)
            if os.path.exists(dec_video): os.remove(dec_video)
            if dec_audio and os.path.exists(dec_audio): os.remove(dec_audio)
            
            return f"Successfully decrypted, merged & saved!"
        except Exception as e:
            return f"Stitching failed: {str(e)}"
