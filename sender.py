import pika
import json
import logging
import threading
import time
import subprocess
import sys
import os
from email_sender import email_alert, sms_alert

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set Pika logger to WARNING to reduce noise
logging.getLogger("pika").setLevel(logging.WARNING)

# Constants
BATCH_SIZE = 100
BATCH_TIMEOUT = 10

# Global variables
message_batches = {
    'koili_ipn_queue': [],
    'email_queue': [],
    'sms_queue': []
}

batch_locks = {
    'koili_ipn_queue': threading.Lock(),
    'email_queue': threading.Lock(),
    'sms_queue': threading.Lock()
}

def run_koili_ipn(amount, machine_identifier):
    script_path = os.path.join(os.path.dirname(__file__), 'koili_ipn.py')
    
    args = [
        sys.executable,
        script_path,
        str(amount),
        machine_identifier
    ]
    
    try:
        subprocess.Popen(args)
    except Exception as e:
        logger.error(f"Error launching koili_ipn script: {str(e)}")

def process_messages(queue_name, messages):
    logger.info(f"Processing {len(messages)} messages from {queue_name}")
    for method, body in messages:
        try:
            # Decode the message body from bytes to string
            message_str = body.decode('utf-8')
            # logger.info(f"Raw message from {queue_name}: {message_str}")
            
            data = json.loads(message_str)
            # logger.info(f"Processed JSON from {queue_name}: {data}")
            
            if queue_name == 'koili_ipn_queue':
                 logger.info(f"Attempting to process koili_ipn for amount: {data['amount']} and machine_identifier: {data['machineIdentifier']}")
                 run_koili_ipn(data['amount'], data['machineIdentifier'])
                 logger.info(f"Finished processing koili_ipn for amount: {data['amount']}")
            elif queue_name == 'email_queue':
                subject = f"Payment Confirmation - {data['merchantId']}"
                body = f"""
                Dear Merchant,

                A payment of Rs{data['amount']} has been received from {data['mobileNumber']}.
                Commission: Rs{data.get('commission', 'N/A')}

                Thank you for using our payment system.
                """
                email_alert(subject, body, data['email'])
                logger.info(f"Sent email for merchant: {data['merchantId']}")
            elif queue_name == 'sms_queue':
                sms_body = f"Payment of Rs{data['amount']} received for merchant {data['merchantId']}"
                sms_alert(sms_body, data['mobileNumber'])
                logger.info(f"Sent SMS to mobile: {data['mobileNumber']}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {queue_name}: {str(e)}")
            logger.error(f"Raw message: {message_str}")
        except KeyError as e:
            logger.error(f"Missing key in message from {queue_name}: {str(e)}")
            logger.error(f"Message content: {data}")
        except Exception as e:
            logger.error(f"Error processing message from {queue_name}: {str(e)}")
            logger.error(f"Raw message: {body}")

def process_batch(channel, queue_name):
    global message_batches
    with batch_locks[queue_name]:
        if message_batches[queue_name]:
            process_messages(queue_name, message_batches[queue_name])
            for method, _ in message_batches[queue_name]:
                try:
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                except pika.exceptions.AMQPChannelError:
                    logger.warning(f"Failed to acknowledge message from {queue_name}. Channel might be closed.")
                    return False
            message_batches[queue_name].clear()
    return True

def check_batch_timer(channel, queue_name):
    while True:
        time.sleep(BATCH_TIMEOUT)
        if not process_batch(channel, queue_name):
            break

def on_message_received(ch, method, properties, body, queue_name):
    global message_batches
    with batch_locks[queue_name]:
        message_batches[queue_name].append((method, body))
    
    if len(message_batches[queue_name]) >= BATCH_SIZE:
        process_batch(ch, queue_name)

def create_channel():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            return connection, channel
        except pika.exceptions.AMQPConnectionError:
            logger.error("Failed to connect. Retrying in 5 seconds...")
            time.sleep(5)

def start_consumer(queue_name):
    while True:
        try:
            connection, channel = create_channel()

            channel.queue_declare(queue=queue_name)
    
            channel.basic_consume(
                queue=queue_name, 
                on_message_callback=lambda ch, method, properties, body: on_message_received(ch, method, properties, body, queue_name),
                auto_ack=False
            )

            # Start the batch timer thread
            timer_thread = threading.Thread(target=check_batch_timer, args=(channel, queue_name), daemon=True)
            timer_thread.start()

            logger.info(f"Started consuming from {queue_name}")
            channel.start_consuming()
        except pika.exceptions.AMQPChannelError as err:
            logger.warning(f"Caught a channel error: {err}, reopening...")
            continue
        except pika.exceptions.AMQPConnectionError:
            logger.warning("Connection was closed, reopening...")
            continue
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as err:
            logger.error(f"Unexpected error: {err}")
            break

if __name__ == "__main__":
    # Start a thread for each queue
    for queue_name in message_batches.keys():
        threading.Thread(target=start_consumer, args=(queue_name,), daemon=True).start()

    logger.info("Sender started. Processing messages from all queues.")

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Sender stopping...")