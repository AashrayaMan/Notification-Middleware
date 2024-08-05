import requests
import json

def make_api_call(amount, machine_identifier):
    api_url = "https://ipn.qrsoundboxnepal.com/api/v1/notify"
    headers = {
        "Content-Type": "application/json",
        "Subscription-Key": "7de9fd42a0b0403ea0e5c73b8deb673b"
    }
    payload = {
        "amount": amount,
        "machineIdentifier": machine_identifier
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            print("API call successful")
            return True, response.json()
        else:
            print(f"API call failed with status code: {response.status_code}")
            return False, response.text
    except Exception as e:
        print(f"An error occurred during API call: {str(e)}")
        return False, str(e)

# Example usage
amount = 3454.35
machine_identifier = "c0eceb97-95ee-4000-8559-5376d74e507a"

success, result = make_api_call(amount, machine_identifier)

if success:
    print("API call was successful")
    print(f"Response data: {result}")
else:
    print("API call failed")
    print(f"Error message: {result}")