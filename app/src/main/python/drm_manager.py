import requests
from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH

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

def get_widevine_keys(wvd_path, pssh_string, license_url, custom_headers=None):
    """
    Automates Widevine key extraction using a .wvd device profile and a license server.
    """
    # Load device profile
    device = Device.load(wvd_path)
    cdm = Cdm.from_device(device)
    
    # Open CDM session
    session_id = cdm.open()
    
    # Prepare PSSH and get challenge
    pssh = PSSH(pssh_string)
    challenge = cdm.get_license_challenge(session_id, pssh)
    
    # Format license headers
    headers = custom_headers or {}
    headers.setdefault("Content-Type", "application/octet-stream")
    
    # Send challenge to license server
    license_res = requests.post(url=license_url, data=challenge, headers=headers, timeout=15)
    license_res.raise_for_status()
    
    # Parse license response
    cdm.parse_license(session_id, license_res.content)
    
    # Extract keys
    keys_list = []
    for key in cdm.get_keys(session_id):
        if key.type == "CONTENT":
            keys_list.append(f"{key.kid.hex}:{key.key.hex()}")
            
    cdm.close(session_id)
    return keys_list
