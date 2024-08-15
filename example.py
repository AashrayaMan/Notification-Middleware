import requests
import random

url = "http://localhost:8000/send_notification"
headers = {
    "Content-Type": "application/json"
}

def generate_transaction(index):
    return {
        "remark1": f"Transaction {index}",
        "retrievalReferenceNumber": f"70112{random.randint(1000, 9999)}",
        "amount": str(random.randint(50, 1000)),
        "merchantId": f"99XXXXXXXXX{random.randint(1, 9)}",
        "terminalId": f"222202XXXXXXXX{random.randint(1, 9)}",
        "type": "alert",
        "uniqueId": f"2023072011410{str(index).zfill(2)}",
        "properties": {
            "txnDate": f"2023-07-{random.randint(1, 31):02d} {random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}",
            "secondaryMobileNumber": f"90123{random.randint(10000, 99999)}",
            "email": "pokharelsamir246@gmail.com",
            "sessionSrlNo": str(random.randint(1, 100)),
            "commission": f"{random.uniform(1, 5):.2f}",
            "initiator": f"98xxxxxxx{random.randint(1, 9)}"
        }
    }

# Generate 100 transactions
transactions = [generate_transaction(i) for i in range(1, 5)]

# Send all transactions at once
response = requests.post(url, json=transactions, headers=headers)
print("Response:", response.json())

print(f"Sent {len(transactions)} transactions")