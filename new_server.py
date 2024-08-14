import pika
import json

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

def on_request_message_received(ch, method, properties, body):
    print(f"Received Request: {properties.correlation_id}")
    print(f"Message:{body}")
    
    # Add message to batch
    global message_batch
    message_batch.append({
        'correlation_id': properties.correlation_id,
        'reply_to': properties.reply_to,
        'body': body.decode()
    })
    
    # If batch size reached or timer expired, process batch
    if len(message_batch) >= BATCH_SIZE:
        process_batch(ch)

def process_batch(ch):
    global message_batch
    if message_batch:
        replies = process_messages(message_batch)
        for reply in replies:
            ch.basic_publish('', 
                             routing_key=reply['reply_to'], 
                             properties=pika.BasicProperties(correlation_id=reply['correlation_id']),
                             body=reply['body'])
        print(f"Processed and sent replies for {len(message_batch)} messages")
        message_batch = []

connection_parameters = pika.ConnectionParameters('localhost')
connection = pika.BlockingConnection(connection_parameters)
channel = connection.channel()

channel.queue_declare(queue='request-queue')

BATCH_SIZE = 100  # Adjust this value based on your needs
message_batch = []

channel.basic_consume(queue='request-queue', auto_ack=True,
    on_message_callback=on_request_message_received)

print("Starting Server")

# Start consuming messages
try:
    channel.start_consuming()
except KeyboardInterrupt:
    # Process any remaining messages in the batch before shutting down
    process_batch(channel)
    channel.stop_consuming()

connection.close()