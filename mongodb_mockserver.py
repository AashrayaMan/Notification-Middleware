from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client['mock_database']
collection = db['mock_collection']

# Insert test documents
test_devices = [
    {
        "fonepay": {
            "merchantId": "1234567890123456",
            "terminalId": "12345678901234567",
        },
        "machineIdentifier": "device-1",
        "enabledServices": ['SMS', 'EMAIL', 'IPN']
    },
    {
        "fonepay": {
            "merchantId": "9876543210987654",
            "terminalId": "98765432109876543",
        },
        "machineIdentifier": "device-2",
        "enabledServices": ['SMS', 'PUSH-NOTIFY']
    }
]

inserted_ids = collection.insert_many(test_devices).inserted_ids
print(f"Inserted test devices with IDs: {inserted_ids}")