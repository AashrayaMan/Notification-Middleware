from service_check import get_device_data, check_enabled_services, send_requirement
from pymongo import MongoClient
from bson.objectid import ObjectId

# Connect to the test database
client = MongoClient('mongodb://localhost:27017/')
db = client['mock_database']
collection = db['mock_collection']

# Insert test data and get valid ObjectIds
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
device_1_id = str(inserted_ids[0])
device_2_id = str(inserted_ids[1])

# Test cases
def test_get_device_data():
    device_data = get_device_data(device_1_id)
    assert device_data is not None
    assert device_data['machineIdentifier'] == 'device-1'
    print("get_device_data test passed")

def test_check_enabled_services():
    device_1_data = get_device_data(device_1_id)
    device_2_data = get_device_data(device_2_id)
    
    assert check_enabled_services(device_1_data, ['SMS', 'EMAIL']) == True
    assert check_enabled_services(device_1_data, ['SMS', 'EMAIL', 'PUSH-NOTIFY']) == False
    assert check_enabled_services(device_2_data, ['SMS', 'PUSH-NOTIFY']) == True
    assert check_enabled_services(device_2_data, ['EMAIL']) == False
    print("check_enabled_services test passed")

def test_send_requirement():
    assert send_requirement(device_1_id, ['SMS', 'EMAIL']) == True
    assert send_requirement(device_1_id, ['SMS', 'EMAIL', 'PUSH-NOTIFY']) == False
    assert send_requirement(device_2_id, ['SMS', 'PUSH-NOTIFY']) == True
    assert send_requirement(device_2_id, ['EMAIL']) == False
    print("send_requirement test passed")

# Run tests
if __name__ == "__main__":
    test_get_device_data()
    test_check_enabled_services()
    test_send_requirement()
    print("All tests passed!")

# Clean up test data
collection.delete_many({"_id": {"$in": inserted_ids}})