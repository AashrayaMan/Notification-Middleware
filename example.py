import requests
import time

url = "http://localhost:8000/send_notification"
headers = {
    "Content-Type": "application/json"
}

# List of different transaction details
transactions = [
    {
        # "mobileNumber": "98xxxxxxx1",
        "remark1": "Transaction 1",
        "retrievalReferenceNumber": "701125451",
        "amount": "100",
        "merchantId": "99XXXXXXXXX1",
        "terminalId": "222202XXXXXXXX1",
        "type": "alert",
        "uniqueId": "202307201141001",
        "properties": {
            "txnDate": "2023-07-22 01:00:10",
            "secondaryMobileNumber": "9012325641",
            "email": "aashraya11@gmail.com",
            "sessionSrlNo": "61",
            "commission": "2.50",
            "initiator": "98xxxxxxx1"
        }
    }
    # Add more transactions as needed
]

for transaction in transactions:
    response = requests.post(url, json=transaction, headers=headers)
    print(f"Response for transaction {transaction['uniqueId']}:", response.json())
    time.sleep(1)  # Wait for 1 second between requests