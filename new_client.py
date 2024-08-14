import pika
import uuid
import logging
import sys
import time
from email_sender import email_alert
import random
import threading
import concurrent.futures

# Configure logging for Pika
logging.getLogger("pika").setLevel(logging.WARNING)

# List of sample merchants
MERCHANTS = [
    {"id": "MERCHANT123", "email": "pokharelsamir246@gmail.com"},
    {"id": "MERCHANT456", "email": "pokharelsamir246@gmail.com"},
    {"id": "MERCHANT789", "email": "pokharelsamir246@gmail.com"},
    # Add more merchants as needed
]

NUM_TRANSACTIONS = 100

def process_transaction(merchant, amount, mobile_number, commission):
    connection_parameters = pika.ConnectionParameters('localhost')
    connection = pika.BlockingConnection(connection_parameters)
    channel = connection.channel()

    reply_queue = channel.queue_declare(queue='', exclusive=True)
    reply_queue_name = reply_queue.method.queue

    def on_reply_message_received(ch, method, properties, body):
        print(f"Reply received for {merchant['id']}: {body}")
        # Send email confirmation
        email_subject = f"Payment Confirmation - {merchant['id']}"
        email_body = f"""
        Dear Merchant,

        A payment of Rs{amount} has been received from {mobile_number}.
        Commission: Rs{commission}

        Thank you for using our payment system.
        """
        email_alert(email_subject, email_body, {merchant['email']})
        channel.stop_consuming()

    channel.basic_consume(queue=reply_queue_name, auto_ack=True,
        on_message_callback=on_reply_message_received)

    channel.queue_declare(queue='request-queue')

    message = f'Transaction: Merchant ID: {merchant["id"]}, Amount: {amount}, Mobile: {mobile_number}, Commission: {commission}'

    cor_id = str(uuid.uuid4())
    print(f"Sending Request for {merchant['id']}: {cor_id}")

    channel.basic_publish('', routing_key='request-queue', properties=pika.BasicProperties(
        reply_to=reply_queue_name,
        correlation_id=cor_id
    ), body=message)

    channel.start_consuming()
    connection.close()

def simulate_transactions():
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_TRANSACTIONS) as executor:
        futures = []
        for _ in range(NUM_TRANSACTIONS):
            merchant = random.choice(MERCHANTS)
            amount = str(random.randint(10, 1000))
            mobile_number = f"98{random.randint(10000000, 99999999)}"
            commission = str(round(float(amount) * 0.02, 2))  # 2% commission

            future = executor.submit(process_transaction, merchant, amount, mobile_number, commission)
            futures.append(future)

        # Wait for all transactions to complete
        concurrent.futures.wait(futures)

if __name__ == "__main__":
    start_time = time.time()
    simulate_transactions()
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nTotal time taken: {total_time:.2f} seconds")
    print(f"Average time per transaction: {total_time/NUM_TRANSACTIONS:.4f} seconds")