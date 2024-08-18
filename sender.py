import pika
import threading
import time
import logging

# Set up logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set Pika logger to WARNING to reduce noise
logging.getLogger("pika").setLevel(logging.WARNING)

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
    
   
    process_individual_message(ch, properties.correlation_id, properties.reply_to, body.decode())

    
    if len(message_batch) >= BATCH_SIZE:
        process_batch(ch)

def process_individual_message(ch, correlation_id, reply_to, body):
    reply = f'Hey its your reply to {correlation_id}'
    ch.basic_publish('', 
                     routing_key=reply_to, 
                     properties=pika.BasicProperties(correlation_id=correlation_id),
                     body=reply)
    
    logger.info(f"Processed and sent reply for individual message: {correlation_id}")

def process_batch(ch):
    global message_batch
    if message_batch:
        replies = process_messages(message_batch)
        for reply in replies:
            ch.basic_publish('', 
                             routing_key=reply['reply_to'], 
                             properties=pika.BasicProperties(correlation_id=reply['correlation_id']),
                             body=reply['body'])
        
        logger.info(f"Processed and sent replies for {len(message_batch)} messages in batch")
        message_batch.clear()

def check_batch_timer():
    global message_batch
    while True:
        time.sleep(BATCH_TIMEOUT)
        if message_batch:
            process_batch(channel)

#For using External Server
# rabbitmq_host = 'your_rabbitmq_host'
# rabbitmq_port = 5672  # Default RabbitMQ port
# rabbitmq_username = 'your_username'
# rabbitmq_password = 'your_password'

# credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
# connection_parameters = pika.ConnectionParameters(host=rabbitmq_host,
#                                                   port=rabbitmq_port,
#                                                   credentials=credentials)

connection_parameters = pika.ConnectionParameters('localhost')
connection = pika.BlockingConnection(connection_parameters)
channel = connection.channel()

channel.queue_declare(queue='request-queue')

BATCH_SIZE = 100 
BATCH_TIMEOUT = 10  
message_batch = []

# Start the batch timer thread
timer_thread = threading.Thread(target=check_batch_timer, daemon=True)
timer_thread.start()

logger.info("Starting Server")

channel.basic_consume(queue='request-queue', auto_ack=True,
    on_message_callback=on_request_message_received)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    process_batch(channel)
    channel.stop_consuming()

connection.close()