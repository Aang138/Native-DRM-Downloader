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

def _has_audio_stream(ffmpeg_bin, path):
    ffprobe_bin = ffmpeg_bin.replace("ffmpeg", "ffprobe")
    probe_bin = ffprobe_bin if os.path.exists(ffprobe_bin) else ffmpeg_bin
    try:
        if probe_bin == ffmpeg_bin:
            res = subprocess.run([ffmpeg_bin, "-i", path], capture_output=True, text=True)
            return "Audio:" in res.stderr
        else:
            res = subprocess.run(
                [probe_bin, "-v", "error", "-select_streams", "a", "-show_entries",
                 "stream=codec_type,codec_name", "-of", "csv=p=0", path],
                capture_output=True, text=True
            )
            return "audio" in res.stdout.strip().lower()
    except Exception:
        return False

def download_selected_stream(url, format_id, manual_key, app_files_dir, callback=None):
    download_path = "/storage/emulated/0/Download/DRM_Downloads"
    os.makedirs(download_path, exist_ok=True)

    log_path = os.path.join(download_path, "debug_log.txt")
    log_lines = []
    def log(msg):
        log_lines.append(str(msg))
        if callback:
            try: callback.onProgress(str(msg))
            except Exception: pass

    def flush_log():
        try:
            with open(log_path, "a") as f:
                f.write("\n--- run " + str(int(time.time())) + " ---\n")
                f.write("\n".join(log_lines) + "\n")
        except Exception:
            pass

    mp4decrypt_bin = os.path.join(app_files_dir, "mp4decrypt")
    ffmpeg_bin = os.path.join(app_files_dir, "ffmpeg")

    if os.path.exists(ffmpeg_bin): os.chmod(ffmpeg_bin, 0o755)
    if os.path.exists(mp4decrypt_bin): os.chmod(mp4decrypt_bin, 0o755)

    # --- DIAGNOSTICS: confirm ffmpeg/mp4decrypt actually exist where we expect ---
    log(f"app_files_dir={app_files_dir}")
    try:
        log(f"Contents of app_files_dir: {os.listdir(app_files_dir)}")
    except Exception as e:
        log(f"Could not list app_files_dir: {e}")
    log(f"ffmpeg_bin path={ffmpeg_bin} exists={os.path.exists(ffmpeg_bin)}")
    log(f"mp4decrypt_bin path={mp4decrypt_bin} exists={os.path.exists(mp4decrypt_bin)}")
    if os.path.exists(ffmpeg_bin):
        log(f"ffmpeg_bin is executable={os.access(ffmpeg_bin, os.X_OK)}")
    # -------------------------------------------------------------------------

    def my_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', '0 KB/s').strip()
            eta = d.get('_eta_str', 'Unknown').strip()
            if callback:
                try: callback.onProgress(f"{p} | {speed} | ETA: {eta}")
                except Exception: pass

    if format_id != "best":
        target_format = f"{format_id}+bestaudio/best"
    else:
        target_format = "best"

    unique_id = int(time.time())
    raw_template = os.path.join(download_path, f'dl_{unique_id}_%(format_id)s.%(ext)s')

    log(f"Starting download. format={target_format} manual_key_provided={bool(manual_key)}")

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
        ydl_opts['ffmpeg_location'] = app_files_dir
        log(f"ffmpeg_location set in ydl_opts = {app_files_dir}")
    else:
        log("WARNING: ffmpeg_bin does not exist — ffmpeg_location NOT set for yt-dlp. "
            "yt-dlp will be unable to merge internally.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        log(f"yt-dlp download exception: {e}")
        flush_log()
        return f"Download failed: {str(e)}"

    session_files = [os.path.join(download_path, f) for f in os.listdir(download_path) if f.startswith(f"dl_{unique_id}")]
    log(f"Session files found: {session_files}")

    if not session_files:
        flush_log()
        return f"Download failed: No files generated."

    video_file = next((f for f in session_files if f.endswith(('.mp4', '.mkv', '.webm')) and 'm4a' not in f and 'opus' not in f and 'aac' not in f), None)
    audio_file = next((f for f in session_files if f.endswith(('.m4a', '.aac', '.opus'))), None)

    if not video_file and session_files:
        video_file = session_files[0]
    if not audio_file:
        audio_file = next((f for f in session_files if f != video_file), None)

    log(f"video_file={video_file}")
    log(f"audio_file={audio_file}")

    if not audio_file:
        log("WARNING: no separate audio file was downloaded at all. "
            "This means yt-dlp only got a video-only stream — "
            "the manifest may serve audio as a separate DASH AdaptationSet "
            "that requires a different key, or bestaudio wasn't selectable for this URL.")

    final_output = os.path.join(download_path, f"playable_{unique_id}.mp4")
    dec_video = None
    dec_audio = None

    # STEP 1: Decrypt files if manual key is provided
    if manual_key and ":" in manual_key and os.path.exists(mp4decrypt_bin):
        log(f"Decrypting with key(s): {manual_key[:8]}...(truncated)")
        dec_video = video_file.replace("dl_", "dec_") if video_file else None
        dec_audio = audio_file.replace("dl_", "dec_") if audio_file else None

        key_args = []
        for pair in manual_key.strip().split(","):
            pair = pair.strip()
            if ":" in pair:
                key_args += ["--key", pair]
        log(f"Parsed {len(key_args)//2} key pair(s) from manual_key")

        try:
            if video_file and os.path.exists(video_file):
                cmd_v = [mp4decrypt_bin] + key_args + [video_file, dec_video]
                res_v = subprocess.run(cmd_v, capture_output=True, text=True)
                log(f"mp4decrypt video returncode={res_v.returncode} stderr={res_v.stderr.strip()[:500]}")
                if res_v.returncode == 0 and os.path.exists(dec_video):
                    video_file = dec_video
                else:
                    log("Video decryption FAILED — keeping original (likely still encrypted) file")

            if audio_file and os.path.exists(audio_file):
                cmd_a = [mp4decrypt_bin] + key_args + [audio_file, dec_audio]
                res_a = subprocess.run(cmd_a, capture_output=True, text=True)
                log(f"mp4decrypt audio returncode={res_a.returncode} stderr={res_a.stderr.strip()[:500]}")
                if res_a.returncode == 0 and os.path.exists(dec_audio):
                    audio_file = dec_audio
                else:
                    log("Audio decryption FAILED — this is likely why audio is missing. "
                        "Check whether the audio track uses a different KID than the video track.")
        except Exception as e:
            log(f"Decryption exception: {e}")
            flush_log()
            return f"Decryption failed: {str(e)}"
    else:
        log("Skipping decryption step (no valid manual_key or mp4decrypt binary missing)")

    # STEP 2: Explicit FFmpeg merge, with full diagnostics
    log("Attempting merge...")
    merge_had_audio = False
    try:
        if video_file and audio_file and os.path.exists(ffmpeg_bin) and os.path.exists(video_file) and os.path.exists(audio_file):
            cmd = [ffmpeg_bin, "-y", "-i", video_file, "-i", audio_file,
                   "-map", "0:v:0", "-map", "1:a:0",
                   "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", final_output]
            res = subprocess.run(cmd, capture_output=True, text=True)
            log(f"Merge attempt 1 (copy) returncode={res.returncode}")
            if res.returncode != 0:
                log(f"Merge attempt 1 stderr: {res.stderr.strip()[-800:]}")
                cmd_reencode = [ffmpeg_bin, "-y", "-i", video_file, "-i", audio_file,
                                 "-map", "0:v:0", "-map", "1:a:0",
                                 "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                                 "-movflags", "+faststart", final_output]
                res = subprocess.run(cmd_reencode, capture_output=True, text=True)
                log(f"Merge attempt 2 (re-encode audio) returncode={res.returncode}")
                if res.returncode != 0:
                    log(f"Merge attempt 2 stderr: {res.stderr.strip()[-800:]}")

            if res.returncode == 0 and os.path.exists(final_output):
                merge_had_audio = _has_audio_stream(ffmpeg_bin, final_output)
                log(f"Final output has audio stream: {merge_had_audio}")
            else:
                log("Both merge attempts failed — falling back to video-only output")
                cmd_fallback = [ffmpeg_bin, "-y", "-i", video_file, "-c", "copy", final_output]
                subprocess.run(cmd_fallback, check=True)
                merge_had_audio = False
        else:
            log(f"Merge SKIPPED. Reason check: video_file_exists={os.path.exists(video_file) if video_file else False} "
                f"audio_file_exists={os.path.exists(audio_file) if audio_file else False} "
                f"ffmpeg_bin_exists={os.path.exists(ffmpeg_bin)}")
            if video_file and os.path.exists(video_file):
                os.rename(video_file, final_output)
            merge_had_audio = False

        for f in session_files:
            if os.path.exists(f): os.remove(f)
        if dec_video and os.path.exists(dec_video): os.remove(dec_video)
        if dec_audio and os.path.exists(dec_audio): os.remove(dec_audio)

        flush_log()
        if merge_had_audio:
            return "Successfully downloaded, merged & saved with audio!"
        else:
            return f"Saved WITHOUT audio — see debug_log.txt in DRM_Downloads for the exact cause"
    except Exception as e:
        log(f"Merging exception: {e}")
        flush_log()
        return f"Merging failed: {str(e)}"
