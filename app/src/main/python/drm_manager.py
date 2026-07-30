import requests

def fetch_with_cloudflare_bypass(url, cookies=None, user_agent=None):
    """
    Performs requests with injected headers/cookies to avoid Cloudflare challenges/404s.
    """
    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
    return response.text

def request_license(license_url, challenge_bytes, custom_headers=None):
    """
    Sends the Widevine license challenge directly to the license server using pure requests.
    """
    headers = custom_headers or {}
    headers.setdefault("Content-Type", "application/octet-stream")
    
    response = requests.post(url=license_url, data=challenge_bytes, headers=headers, timeout=15)
    response.raise_for_status()
    return response.content
