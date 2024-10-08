import pika
import json
import threading
import subprocess
import sys
import os
import logging
from email_sender import email_alert, sms_alert

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def publish_message(queue_name, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.basic_publish(exchange='', routing_key=queue_name, body=message)
    connection.close()
    logger.info(f"Published message to {queue_name}")

def process_koili_ipn(ch, method, properties, body):
    try:
        data = json.loads(body)
        script_path = os.path.abspath('koili_ipn.py')
        
        result = subprocess.run([sys.executable, script_path, str(data['amount']), str(data['machineIdentifier'])], 
                                capture_output=True, text=True, check=True)
        
        logger.info(f"koili_ipn.py output: {result.stdout}")
        logger.info(f"Processed koili_ipn for amount: {data['amount']}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing koili_ipn.py: {e}")
        logger.error(f"koili_ipn.py stderr: {e.stderr}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def process_email(ch, method, properties, body):
    try:
        data = json.loads(body)
        email_subject = f"Payment Confirmation - {data['merchantId']}"
        email_body = f"""
        Dear Merchant,

        A payment of Rs{data['amount']} has been received from {data['mobileNumber']}.
        Commission: Rs{data.get('commission', 'N/A')}

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

def start_consumer(queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.basic_consume(
        queue=queue_name, 
        on_message_callback=globals()[f"process_{queue_name.split('_')[0]}"],
        auto_ack=False
    )
    logger.info(f"Started consuming from {queue_name}")
    channel.start_consuming()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = sys.argv[1]
        data = json.loads(message)
        enabled_services = data['enabledServices']
        
        # Start only the enabled queues
        for service in enabled_services:
            if service == 'EMAIL':
                threading.Thread(target=start_consumer, args=('email_queue',)).start()
            elif service == 'SMS':
                threading.Thread(target=start_consumer, args=('sms_queue',)).start()
            elif service == 'IPN':
                threading.Thread(target=start_consumer, args=('koili_ipn_queue',)).start()
        
        # Publish messages to enabled queues
        if 'IPN' in enabled_services:
            publish_message('koili_ipn_queue', message)
        if 'EMAIL' in enabled_services and data.get('email'):
            publish_message('email_queue', message)
        if 'SMS' in enabled_services:
            publish_message('sms_queue', message)
    
    logger.info("Enabled consumers started. Waiting for messages.")