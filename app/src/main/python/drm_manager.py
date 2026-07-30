import requests
import yt_dlp

def fetch_with_cloudflare_bypass(url, cookies=None, user_agent=None):
    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
    return response.text

def fetch_keys_via_api(api_url, pssh_string, license_url, token=None):
    payload = {
        "pssh": pssh_string,
        "license_url": license_url,
        "token": token
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(api_url, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data.get("keys", [])

def get_media_streams(url, user_agent=None):
    """
    Extracts available video resolutions and audio language tracks separately 
    without downloading, for user selection.
    """
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
    }
    if user_agent:
        ydl_opts['http_headers'] = {'User-Agent': user_agent}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        
        video_options = []
        audio_options = []
        
        for f in formats:
            format_id = f.get('format_id')
            ext = f.get('ext')
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            language = f.get('language') or f.get('language_preference') or 'Original'
            format_note = f.get('format_note', '')
            height = f.get('height')
            
            # Separate Video Streams
            if vcodec != 'none' and height:
                label = f"{height}p - {ext} ({format_note})" if format_note else f"{height}p - {ext}"
                video_options.append({
                    "format_id": format_id,
                    "label": label
                })
            
            # Separate Audio Streams (Multilingual Tracks like Tamil, Hindi, English)
            elif vcodec == 'none' and acodec != 'none':
                lang_label = f"{language.upper()} - {ext} ({format_note})" if format_note else f"{language.upper()} - {ext}"
                audio_options.append({
                    "format_id": format_id,
                    "label": lang_label
                })
                
        return {
            "videos": video_options,
            "audios": audio_options
        }
