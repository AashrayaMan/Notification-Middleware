import pika
import uuid
from email_sender import email_alert, sms_alert
import logging
import sys

# Configure logging for Pika
logging.getLogger("pika").setLevel(logging.WARNING)

# Get transaction details from command-line arguments
merchant_id = sys.argv[1]
amount = sys.argv[2]
mobile_number = sys.argv[3]
email = sys.argv[4]
commission = sys.argv[5]

def on_reply_message_received(ch, method, properties, body):
    print(f"reply received: {body}")
    email_alert("KOILITEAM",
                f"Merchant-id:{merchant_id} Rs{amount} has been received.",
                {email})
    channel.stop_consuming()

connection_parameters = pika.ConnectionParameters('localhost')

connection = pika.BlockingConnection(connection_parameters)

channel = connection.channel()

reply_queue = channel.queue_declare(queue=f'merchant-id:{merchant_id}', exclusive=True)

channel.basic_consume(queue=reply_queue.method.queue, auto_ack=True,
    on_message_callback=on_reply_message_received)

channel.queue_declare(queue='request-queue')

message = f'Transaction: Merchant ID: {merchant_id}, Amount: {amount}, Mobile: {mobile_number}, Commission: {commission}'

cor_id = str(uuid.uuid4())
print(f"Sending Request: {cor_id}")

channel.basic_publish('', routing_key='request-queue', properties=pika.BasicProperties(
    reply_to=reply_queue.method.queue,
    correlation_id=cor_id
), body=message)

print("Starting Client")

channel.start_consuming()