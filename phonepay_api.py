import requests
import json
import hmac
import hashlib
import base64
import uuid
import logging
from requests.exceptions import RequestException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FonepayNotificationAPI:
    def __init__(self, base_url, api_key, api_secret):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logging.getLogger(__name__)

    def generate_signature(self, nonce, body):
        signature_data = f" {self.api_key} {nonce} {body} "
        hmac_obj = hmac.new(self.api_secret.encode(), signature_data.encode(), hashlib.sha512)
        return base64.b64encode(hmac_obj.digest()).decode()

    def send_notification(self, payload):
        url = f"{self.base_url}/notification/send"
        
        body = json.dumps(payload, separators=(',', ':'))
        nonce = str(uuid.uuid4())
        signature = self.generate_signature(nonce, body)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'HmacSHA512 {self.api_key}:{nonce}:{signature}'
        }
        
        try:
            response = requests.post(url, data=body, headers=headers, timeout=10)
            response.raise_for_status()
            self.logger.info(f"Send Notification Status Code: {response.status_code}")
            return response.json()
        except RequestException as e:
            self.logger.error(f"An error occurred while sending notification: {e}")
            return None

    def get_last_5_transactions(self, merchant_id, terminal_id):
        url = f"{self.base_url}/callback"
        
        payload = {
            "merchantId": merchant_id,
            "terminalId": terminal_id
        }
        
        body = json.dumps(payload, separators=(',', ':'))
        nonce = str(uuid.uuid4())
        signature = self.generate_signature(nonce, body)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'HmacSHA512 {self.api_key}:{nonce}:{signature}'
        }
        
        try:
            response = requests.post(url, data=body, headers=headers, timeout=10)
            response.raise_for_status()
            self.logger.info(f"Callback Status Code: {response.status_code}")
            return response.json()
        except RequestException as e:
            self.logger.error(f"An error occurred while getting transactions: {e}")
            return None

# Usage
if __name__ == "__main__":
    base_url = "http://localhost:5000"  # Our mock server URL
    api_key = "test@test.com.np"  # Must match the mock server
    api_secret = "testApiSecret"  # Must match the mock server

    api = FonepayNotificationAPI(base_url, api_key, api_secret)

    # Send Notification
    notification_payload = {
        "mobileNumber": "98xxxxxxxx",
        "remark1": "Message to send",
        "retrievalReferenceNumber": "701125454",
        "amount": "400",
        "merchantId": "99XXXXXXXXXX",
        "terminalId": "222202XXXXXXXXXX",
        "type": "alert",
        "uniqueId": "202307201141001",
        "properties": {
            "txnDate": "2023-07-22 01:00:10",
            "secondaryMobileNumber": "9012325645",
            "email": "cn@fpay.com",
            "sessionSrlNo": "69",
            "commission": "10.00",
            "initiator": "98xxxxxxxx"
        }
    }

    notification_response = api.send_notification(notification_payload)
    if notification_response:
        logging.info(f"Notification Response: {json.dumps(notification_response, indent=2)}")

    # Get Last 5 Transactions
    transactions_response = api.get_last_5_transactions("99XXXXXXXXXX", "222202XXXXXXXXXX")
    if transactions_response:
        logging.info(f"Transactions Response: {json.dumps(transactions_response, indent=2)}")