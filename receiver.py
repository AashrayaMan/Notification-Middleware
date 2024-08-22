import pika
import json
import threading
import subprocess
import sys
import os
import logging
from email_sender import email_alert, sms_alert

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_koili_ipn(ch, method, properties, body):
    try:
        data = json.loads(body)
        script_path = os.path.join(os.path.dirname(__file__), 'koili_ipn.py')
        subprocess.Popen([sys.executable, script_path, str(data['amount'])])
        logger.info(f"Processed koili_ipn for amount: {data['amount']}")
    except Exception as e:
        logger.error(f"Error processing koili_ipn: {str(e)}")
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

def process_email(ch, method, properties, body):
    try:
        data = json.loads(body)
        email_subject = f"Payment Confirmation - {data['merchantId']}"
        email_body = f"""
        Dear Merchant,

        A payment of Rs{data['amount']} has been received from {data['mobileNumber']}.
        Commission: Rs{data['commission']}

        Thank you for using our payment system.
        """
        email_alert(email_subject, email_body, data['email'])
        logger.info(f"Processed email for merchant: {data['merchantId']}")
    except Exception as e:
        logger.error(f"Error processing email: {str(e)}")
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

def process_sms(ch, method, properties, body):
    try:
        data = json.loads(body)
        sms_body = f"Payment of Rs{data['amount']} received for merchant {data['merchantId']}"
        sms_alert(sms_body, data['mobileNumber'])
        logger.info(f"Processed SMS for mobile: {data['mobileNumber']}")
    except Exception as e:
        logger.error(f"Error processing SMS: {str(e)}")
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer(queue_name, callback):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    logger.info(f"Started consuming from {queue_name}")
    channel.start_consuming()

if __name__ == "__main__":
    # Start threads for each queue
    threading.Thread(target=start_consumer, args=('koili_ipn_queue', process_koili_ipn)).start()
    threading.Thread(target=start_consumer, args=('email_queue', process_email)).start()
    threading.Thread(target=start_consumer, args=('sms_queue', process_sms)).start()

    logger.info("All consumers started. Waiting for messages.")