from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client['mock_database']
collection = db['mock_collection']

# Insert test documents
test_devices = [
    
    {
        "fonepay": {
            "merchantId": "987654321000987654",
            "terminalId": "9876543210900876543",
        },
        "machineIdentifier": "c0eceb97-95ee-4000-8559-5376d74e507a",
        "enabledServices": ['IPN']
    },
     {
        "fonepay": {
            "merchantId": "9876543210010987654",
            "terminalId": "98765432109100876543",
        },
        "machineIdentifier": "c0eceb97-95ee-4000-8559-5376d74e507a",
        "enabledServices": ['EMAIL']
    }, {
        "fonepay": {
            "merchantId": "9876543210030987654",
            "terminalId": "9876543210900876543",
        },
        "machineIdentifier": "c0eceb97-95ee-4000-8559-5376d74e507a",
        "enabledServices": ['IPN','EMAIL']
    }
    
]

inserted_ids = collection.insert_many(test_devices).inserted_ids
print(f"Inserted test devices with IDs: {inserted_ids}")