import yt_dlp

def get_stream_options(url):
    ydl_opts = {
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            title = info.get('title', 'Protected Stream')
            
            output = [
                f"Title: {title}",
                f"Total Formats Found: {len(formats)}"
            ]
            
            video_resolutions = set()
            audio_languages = set()
            
            for f in formats:
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                resolution = f.get('resolution') or f.get('format_note')
                
                if vcodec != 'none' and resolution:
                    video_resolutions.add(str(resolution))
                if acodec != 'none':
                    lang = f.get('language') or f.get('audio_ext') or 'Default'
                    audio_languages.add(str(lang))
                    
            output.append(f"Resolutions: {', '.join(video_resolutions) if video_resolutions else 'Adaptive Manifest'}")
            output.append(f"Audio Tracks: {', '.join(audio_languages) if audio_languages else 'Standard Audio'}")
            output.append("Status: Ready for decryption & download.")
            
            return "\n".join(output)
            
    except Exception as e:
        return f"Failed to parse stream: {str(e)}"
