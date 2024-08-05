import pika

def on_request_message_received(ch, method, properties, body):
    print(f"Received Request: {properties.correlation_id}")
    print(f"Message:{body}")
    ch.basic_publish('', routing_key=properties.reply_to, body = f'Hey its your reply to {properties.correlation_id}')


connection_parameters = pika.ConnectionParameters('localhost')

# # Replace 'localhost' with the IP address or hostname of your RabbitMQ server
# server_address = 'your_rabbitmq_server_address'
# # Add credentials if required
# credentials = pika.PlainCredentials('your_username', 'your_password')

# connection_parameters = pika.ConnectionParameters(
#     host=server_address,
#     credentials=credentials,
#     # Add any other necessary parameters like port, virtual_host, etc.
# )

connection = pika.BlockingConnection(connection_parameters)

channel = connection.channel()

channel.queue_declare(queue='request-queue')

channel.basic_consume(queue='request-queue', auto_ack=True,
    on_message_callback=on_request_message_received)

print("Starting Server")

channel.start_consuming()