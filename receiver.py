import pika
import uuid
import logging
import sys
from email_sender import email_alert

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure logging for Pika
logging.getLogger("pika").setLevel(logging.WARNING)

# Get transaction details from command-line arguments
merchant_id = sys.argv[1]
amount = sys.argv[2]
mobile_number = sys.argv[3]
email = sys.argv[4]
commission = sys.argv[5]

connection_parameters = pika.ConnectionParameters('localhost')
connection = pika.BlockingConnection(connection_parameters)
channel = connection.channel()

reply_queue = channel.queue_declare(queue=f'merchant-id:{merchant_id}', auto_delete=True)
reply_queue_name = reply_queue.method.queue

def on_reply_message_received(ch, method, properties, body):
    try:
        logger.info(f"Reply received for {merchant_id}: {body}")
        # Send email confirmation
        email_subject = f"Payment Confirmation - {merchant_id}"
        email_body = f"""
        Dear Merchant,

        A payment of Rs{amount} has been received from {mobile_number}.
        Commission: Rs{commission}

        Thank you for using our payment system.
        """
        email_alert(email_subject, email_body, {email})
    finally:
        channel.stop_consuming()        

channel.basic_consume(queue=reply_queue_name, auto_ack=True,
        on_message_callback=on_reply_message_received)

channel.queue_declare(queue='request-queue')

message =f'Transaction: Merchant ID: {merchant_id}, Amount: {amount}, Mobile: {mobile_number}, Commission: {commission}'

cor_id = str(uuid.uuid4())
logger.info(f"Sending Request for {merchant_id}: {cor_id}")

channel.basic_publish('', routing_key='request-queue', properties=pika.BasicProperties(
        reply_to=reply_queue_name,
        correlation_id=cor_id
    ), body=message)

channel.start_consuming()
connection.close()