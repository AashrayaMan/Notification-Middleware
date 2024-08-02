import requests
import hmac
import hashlib
import time
import base64

def request_api_with_hmac(url, method, payload, secret_key):
    timestamp = str(int(time.time()))
    
    string_to_sign = f"{method}\n{url}\n{timestamp}\n{payload}"
    
    # Create the HMAC signature using SHA-512 and encode it in Base64
    signature = base64.b64encode(
        hmac.new(
            secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha512  # Changed to SHA-512
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

# Example usage
url = 'https://api.example.com/endpoint'
method = 'POST'
payload = '{"key": "value"}'
secret_key = '7de9fd42a0b0403ea0e5c73b8deb673b'

response = request_api_with_hmac(url, method, payload, secret_key)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")