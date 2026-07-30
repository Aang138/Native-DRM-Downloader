import os
from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH

def fetch_keys(pssh_string, license_url):
    try:
        # Load your device .wvd file if placed in this same python folder
        device_path = os.path.join(os.path.dirname(__file__), "device.wvd")
        if not os.path.exists(device_path):
            return "Error: .wvd device file missing in python assets"

        device = Device.load(device_path)
        cdm = Cdm.from_device(device)
        session_id = cdm.open()
        
        pssh = PSSH(pssh_string)
        challenge = cdm.get_license_challenge(session_id, pssh)
        
        # Here you would typically use 'requests' to post challenge to license_url
        # and parse keys using cdm.parse_license(license_request)
        
        cdm.close(session_id)
        return "Key_ID:Placeholder_Decryption_Key"
    except Exception as e:
        return f"Error: {str(e)}"
