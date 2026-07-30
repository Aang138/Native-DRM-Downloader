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

def fetch_keys_via_api(api_url, pssh_string, license_url, token=None):
    """
    Sends the license details to your external backend service 
    to retrieve decrypted keys safely without local dependency conflicts.
    """
    payload = {
        "pssh": pssh_string,
        "license_url": license_url,
        "token": token
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(api_url, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    
    # Expecting JSON response like: {"keys": ["kid1:key1", "kid2:key2"]}
    data = response.json()
    return data.get("keys", [])
