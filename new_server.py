import pika
import json
import threading
import time
from email_sender import email_alert

def process_messages(messages):
    # Process all messages and generate replies
    replies = []
    for msg in messages:
        reply = f'Hey its your reply to {msg["correlation_id"]}'
        replies.append({
            'correlation_id': msg['correlation_id'],
            'reply_to': msg['reply_to'],
            'body': reply
        })
    return replies

def send_email(merchant_id, amount, mobile_number, commission, email):
    email_subject = f"Payment Confirmation - {merchant_id}"
    email_body = f"""
    Dear Merchant,

    A payment of Rs{amount} has been received from {mobile_number}.
    Commission: Rs{commission}

    Thank you for using our payment system.
    """
    email_alert(email_subject, email_body, email)

def on_request_message_received(ch, method, properties, body):
    print(f"Received Request: {properties.correlation_id}")
    print(f"Message: {body}")
    
    # Parse the message body
    message_data = body.decode().split(', ')
    merchant_id = message_data[0].split(': ')[1]
    amount = message_data[1].split(': ')[1]
    mobile_number = message_data[2].split(': ')[1]
    commission = message_data[3].split(': ')[1]
    
    # Add message to batch
    message_batch.append({
        'correlation_id': properties.correlation_id,
        'reply_to': properties.reply_to,
        'body': body.decode(),
        'merchant_id': merchant_id,
        'amount': amount,
        'mobile_number': mobile_number,
        'commission': commission
    })
    
    # Process individual message immediately
    process_individual_message(ch, properties.correlation_id, properties.reply_to, body.decode(), 
                               merchant_id, amount, mobile_number, commission)
    
    # If batch size reached, process batch
    if len(message_batch) >= BATCH_SIZE:
        process_batch(ch)

def process_individual_message(ch, correlation_id, reply_to, body, merchant_id, amount, mobile_number, commission):
    reply = f'Hey its your reply to {correlation_id}'
    ch.basic_publish('', 
                     routing_key=reply_to, 
                     properties=pika.BasicProperties(correlation_id=correlation_id),
                     body=reply)
    print(f"Processed and sent reply for individual message: {correlation_id}")
    
    # Send email for individual message
    send_email(merchant_id, amount, mobile_number, commission, "merchant@example.com")  # Replace with actual email

def process_batch(ch):
    global message_batch
    if message_batch:
        replies = process_messages(message_batch)
        for reply in replies:
            ch.basic_publish('', 
                             routing_key=reply['reply_to'], 
                             properties=pika.BasicProperties(correlation_id=reply['correlation_id']),
                             body=reply['body'])
        
        # Send emails for batch
        for msg in message_batch:
            send_email(msg['merchant_id'], msg['amount'], msg['mobile_number'], msg['commission'], "merchant@example.com")  # Replace with actual email
        
        print(f"Processed and sent replies for {len(message_batch)} messages in batch")
        message_batch.clear()

def check_batch_timer():
    global message_batch
    while True:
        time.sleep(BATCH_TIMEOUT)
        if message_batch:
            process_batch(channel)

connection_parameters = pika.ConnectionParameters('localhost')
connection = pika.BlockingConnection(connection_parameters)
channel = connection.channel()

channel.queue_declare(queue='request-queue')

BATCH_SIZE = 100  # Adjust this value based on your needs
BATCH_TIMEOUT = 60  # Process batch every 60 seconds if not full
message_batch = []

# Start the batch timer thread
timer_thread = threading.Thread(target=check_batch_timer, daemon=True)
timer_thread.start()

channel.basic_consume(queue='request-queue', auto_ack=True,
    on_message_callback=on_request_message_received)

print("Starting Server")

try:
    channel.start_consuming()
except KeyboardInterrupt:
    # Process any remaining messages in the batch before shutting down
    process_batch(channel)
    channel.stop_consuming()

connection.close()