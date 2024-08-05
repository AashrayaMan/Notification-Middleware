import requests
import time
import hmac
import hashlib
import base64
import json

def request_api_with_hmac(url, method, payload, secret_key):
    timestamp = str(int(time.time()))
    
    parsed_url = requests.utils.urlparse(url)
    path = parsed_url.path or "/"
    
    string_to_sign = f"{method}\n{path}\n{timestamp}\n{payload}"
    print(f"Client string to sign: {string_to_sign}")  # Debug print
    
    signature = base64.b64encode(
        hmac.new(
            secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha512
        ).digest()
    ).decode('utf-8')
    
    headers = {
        'Content-Type': 'application/json',
        'X-Timestamp': timestamp,
        'X-Signature': signature
    }
    
    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'POST':
        response = requests.post(url, headers=headers, data=payload)
    else:
        raise ValueError("Unsupported HTTP method")
    
    return response

url = ' https://ipn-staging.qrsoundboxnepal.com'
method = 'GET'
payload = ''
secret_key = '7de9fd42a0b0403ea0e5c73b8deb673b'

response = request_api_with_hmac(url, method, payload, secret_key)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
demo = response.text
res  = json.loads(demo)

# Ph_no = res["number"]
# Email = res["email"]
# merchant_id = res["merchant_id"]