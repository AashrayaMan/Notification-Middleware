import requests
import json
from dotenv import load_dotenv
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
# API endpoint URL
url = os.getenv('API_ENDPOINT')

# Headers
headers = {
    "Content-Type": "application/json",
    "Subscription-Key": "36918384da4b491986a08f38b424edd3"
}

def main(amount):
    # Payload data
    payload = {
        "amount": float(amount),
        "machineIdentifier": "c0eceb97-95ee-4000-8559-5376d74e507a"
    }

    # Make the POST request
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # Check the response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Message: {result['message']}")
            logger.info(f"Response Code: {result['responseCode']}")
        else:
            logger.error(f"Error: Status Code {response.status_code}")
            logger.error(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.error("Usage: python koili_ipn.py <amount>")
        sys.exit(1)
    
    amount = sys.argv[1]
    main(amount)