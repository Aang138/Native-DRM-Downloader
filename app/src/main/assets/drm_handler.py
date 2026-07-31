import requests

def fetch_crunchyroll_manifest(mpd_url, session_cookie=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.crunchyroll.com/"
    }
    if session_cookie:
        headers["Cookie"] = f"session_id={session_cookie}"
    response = requests.get(mpd_url, headers=headers, allow_redirects=True)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch manifest. Status code: {response.status_code}")
