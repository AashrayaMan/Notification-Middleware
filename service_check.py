from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mock_database']
collection = db['mock_collection']

def get_device_data(device_id):
    """Retrieve device data from MongoDB."""
    try:
        return collection.find_one({"_id": ObjectId(device_id)})
    except InvalidId:
        print(f"Invalid device ID: {device_id}")
        return None

def check_enabled_services(device_data, required_services):
    """Check if all required services are enabled for the device."""
    if not device_data or 'enabledServices' not in device_data:
        return False
    
    enabled_services = set(device_data['enabledServices'])
    required_services = set(required_services)
    
    return required_services.issubset(enabled_services)

def send_requirement(device_id, services):
    """Send requirement if all specified services are enabled."""
    device_data = get_device_data(device_id)
    
    if device_data is None:
        return False

    if check_enabled_services(device_data, services):
        print(f"Sending requirement for device {device_id}. All required services are enabled.")
        # Add your code here to send the actual requirement
        return True
    else:
        print(f"Cannot send requirement for device {device_id}. Not all required services are enabled.")
        return False

# Remove or comment out the example usage
# device_id = "60a7b2b9e4b0a1234567890"  # This line was causing the error
# required_services = ['SMS', 'EMAIL']
# result = send_requirement(device_id, required_services)
# if result:
#     print("Requirement sent successfully.")
# else:
#     print("Failed to send requirement.")