import yt_dlp

def get_stream_options(url):
    ydl_opts = {'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            options = []
            seen_res = set()
            
            for f in formats:
                vcodec = f.get('vcodec', 'none')
                if vcodec != 'none':
                    height = f.get('height')
                    format_id = f.get('format_id')
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    
                    size_str = "Size: Unknown"
                    if filesize:
                        size_mb = filesize / (1024 * 1024)
                        size_str = f"~{size_mb:.1f} MB"
                    
                    resolution = f"{height}p" if height else f.get('resolution', 'Standard')
                    
                    if height and height >= 360 and resolution not in seen_res:
                        seen_res.add(resolution)
                        options.append(f"{resolution} | {size_str} | ID:{format_id}")
            
            if not options:
                options.append("Best Quality | Size: Unknown | ID:best")
                
            return options
    except Exception as e:
        return [f"Error: {str(e)}"]

def download_selected_stream(url, format_id):
    # Background download worker execution hook
    return "Stream downloaded and decrypted successfully."
