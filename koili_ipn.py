import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
# API endpoint URL
url = os.getenv('API_ENDPOINT')

# Headers
headers = {
    "Content-Type": "application/json",
    "Subscription-Key": "36918384da4b491986a08f38b424edd3"
}

# Payload data
payload = {
    "amount": os.getenv('AMOUNT'),
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