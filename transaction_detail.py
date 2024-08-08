import requests

def get_transactions(merchant_id, terminal_id):
    url = f"http://localhost:8000/get_transactions/{merchant_id}/{terminal_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        transaction_details = response.json()
        return transaction_details
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

merchant_id = "your_merchant_id"
terminal_id = "your_terminal_id"
transaction_details = get_transactions(merchant_id, terminal_id)

if transaction_details:
    print(transaction_details)
    # Assuming there's at least one transaction in the list
    first_transaction = transaction_details.get("transaction_details", [])[0]
    amount = first_transaction.get("amount")
    print(amount)
else:
    print("Failed to retrieve transaction details")
