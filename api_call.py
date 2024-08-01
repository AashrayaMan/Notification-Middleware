import requests
import hmac
import hashlib
import time

def make_api_request(url, method, payload, secret_key):
    # Convert secret_key to bytes
    secret_key = secret_key.encode('utf-8')

    # Create a timestamp
    timestamp = str(int(time.time()))

    # Combine the elements to be signed
    string_to_sign = f"{method}\n{url}\n{timestamp}\n{payload}"
    
    # Create the HMAC signature
    signature = hmac.new(secret_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # Prepare headers
    headers = {
        'Content-Type': 'application/json',
        'X-Timestamp': timestamp,
        'X-Signature': signature
    }

    # Make the request
    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'POST':
        response = requests.post(url, headers=headers, data=payload)
    # Add other methods as needed

    return response

# Example usage
url = 'https://api.example.com/endpoint'
method = 'POST'
payload = '{"key": "value"}'
secret_key = 'your_secret_key'

response = make_api_request(url, method, payload, secret_key)
print(response.status_code)
print(response.text)