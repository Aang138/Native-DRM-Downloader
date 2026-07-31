import os
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
    video_formats = []
    audio_tracks = {}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [info])
            
            for f in formats:
                format_id = f.get('format_id')
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                ext = f.get('ext', 'mp4')
                resolution = f.get('resolution', f.get('format_note', 'HD'))
                
                # Collect video streams
                if vcodec != 'none':
                    filesize = f.get('filesize', f.get('filesize_approx', 0))
                    size_mb = round(filesize / (1024 * 1024), 2) if filesize else "?"
                    video_formats.append({
                        'id': format_id,
                        'res': resolution,
                        'size': size_mb,
                        'ext': ext
                    })
                
                # Collect audio streams and detect language
                if vcodec == 'none' and acodec != 'none':
                    lang = f.get('language') or f.get('format_note') or f.get('language_preference') or "unknown"
                    lang_lower = str(lang).lower()
                    
                    if 'ta' in lang_lower or 'tamil' in lang_lower:
                        lang_name = "Tamil"
                    elif 'te' in lang_lower or 'telugu' in lang_lower:
                        lang_name = "Telugu"
                    elif 'hi' in lang_lower or 'hindi' in lang_lower:
                        lang_name = "Hindi"
                    elif 'en' in lang_lower or 'english' in lang_lower:
                        lang_name = "English"
                    elif 'ml' in lang_lower or 'malayalam' in lang_lower:
                        lang_name = "Malayalam"
                    elif 'kn' in lang_lower or 'kannada' in lang_lower:
                        lang_name = "Kannada"
                    else:
                        lang_name = str(lang).upper()
                        
                    audio_tracks[format_id] = lang_name

            # Pair video resolutions with available audio language tracks
            if video_formats and audio_tracks:
                for v in video_formats:
                    for a_id, a_lang in audio_tracks.items():
                        desc = f"Res: {v['res']} | Lang: {a_lang} | Size: {v['size']}MB | ID:{v['id']}+{a_id}"
                        options.append(desc)
            elif video_formats:
                for v in video_formats:
                    desc = f"Res: {v['res']} | Size: {v['size']}MB | ID:{v['id']}+bestaudio"
                    options.append(desc)
            else:
                options.append("Best Quality Available | ID:best")
                
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
                    callback.onProgress("Merging video & audio tracks...")
                except Exception:
                    pass

    ydl_opts = {
        'format': format_id,
        'allow_unplayable_formats': True,
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'progress_hooks': [my_hook],
        'merge_output_format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return f"Saved with selected audio language to -> Download/DRM_Downloads"
    except Exception as e:
        return f"Download failed: {str(e)}"
