import pika
import uuid
from email_sender import email_alert,sms_alert
from phonepay_api import email,amount,merchant_id
import subprocess

def on_reply_message_received(ch, method, properties, body):
    print(f"reply recieved: {body}")
    email_alert("KOILITEAM",
                f"Merchant-id:{merchant_id} Rs{amount} has been received.",
                {email})
    channel.stop_consuming()

def run_another_script():
    subprocess.run(["python", "api_call.py"], check=True)

run_another_script()

connection_parameters = pika.ConnectionParameters('localhost')

connection = pika.BlockingConnection(connection_parameters)

channel = connection.channel()

reply_queue = channel.queue_declare(queue=f'merchant-id:{merchant_id}', exclusive=True)

channel.basic_consume(queue=reply_queue.method.queue, auto_ack=True,
    on_message_callback=on_reply_message_received)

channel.queue_declare(queue='request-queue')

message = 'Can I request a reply?'

cor_id = str(uuid.uuid4())
print(f"Sending Request: {cor_id}")

channel.basic_publish('', routing_key='request-queue', properties=pika.BasicProperties(
    reply_to=reply_queue.method.queue,
    correlation_id=cor_id
), body=message)

print("Starting Client")

channel.start_consuming()