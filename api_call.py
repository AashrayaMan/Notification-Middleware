import requests
import json

# API endpoint URL
url = "https://ipn-staging.qrsoundboxnepal.com/api/v1/notify"

# Headers
headers = {
    "Content-Type": "application/json",
    "Subscription-Key": "7de9fd42a0b0403ea0e5c73b8deb673b"
}

# Payload data
payload = {
    "amount": 3454.35,
    "machineIdentifier": "c0eceb97-95ee-4000-8559-5376d74e507a"
}

# Make the POST request
try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    # Check the response
    if response.status_code == 200:
        result = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Message: {result['message']}")
        print(f"Response Code: {result['responseCode']}")
    else:
        print(f"Error: Status Code {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")