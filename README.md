# Koili Notification Middleware

## Introduction

The Koili Notification Middleware is a robust solution designed to handle transaction notifications for Fonepay, a digital payment platform. This system integrates with Fonepay's API to send notifications and retrieve transaction details, while also implementing asynchronous processing using RabbitMQ for improved scalability and reliability.

Key features include:
- RESTful API for sending notifications and retrieving transaction data
- Asynchronous processing of transactions using RabbitMQ
- Email and SMS notifications for successful transactions
- Mock server for testing and development purposes
- Comprehensive error handling and logging

## Table of Contents

1. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Configuration](#configuration)
2. [System Architecture](#system-architecture)
3. [Usage](#usage)
   - [Starting the Servers](#starting-the-servers)
   - [API Endpoints](#api-endpoints)
4. [Component Details](#component-details)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)
8. [License](#license)
9. [Contact](#contact)

## Getting Started

### Prerequisites

- Python 3.7+
- RabbitMQ server
- SMTP server access (for email notifications)
- Twilio account (for SMS notifications)

### Installation

1. Clone the repository: 
https://dev.azure.com/BitsKraft/Koili%20(IPN%20Platform)/_git/koili-notification-middleware?version=GBmain

2. Run rabbit mq on Cmd:
docker run -d --name rabbitmq --restart always -p 5672:5672 -p 15672:15672 rabbitmq:3.13.4-management

3. Install the required dependencies:
pip install -r requirements.txt


### Configuration

1. RabbitMQ Configuration:
- Update the connection parameters in `sender.py` and `receiver.py`:
  ```python
  connection_parameters = pika.ConnectionParameters('localhost')
  ```
- If using a remote RabbitMQ server, update with appropriate credentials:
  ```python
  server_address = 'your_rabbitmq_server_address'
  credentials = pika.PlainCredentials('your_username', 'your_password')
  connection_parameters = pika.ConnectionParameters(host=server_address, credentials=credentials)
  ```

2. Fonepay API Configuration:
- Update the API key and secret in `.env`:
  ```python
  api_key = "your_api_key"
  api_secret = "your_api_secret"
  ```

3. Email Configuration:
- Update the email settings in `.env`:
  ```python
  user = "your_email@gmail.com"
  password = "your_email_password"
  ```

4. SMS Configuration:
- Update the Twilio credentials in `.env`:
  ```python
  account_sid = 'your_account_sid'
  auth_token = 'your_auth_token'
  ```

## System Architecture

The system consists of several interconnected components:

1. FastAPI Server (`main.py`): Handles incoming API requests, interacts with the Fonepay API, and enqueues transactions for processing.
2. RabbitMQ receiver (`receiver`): Processes transactions asynchronously, sending email and SMS notifications.
3. RabbitMQ Server (`sender.py`): Consumes messages from the queue and handles responses.
4. Notification Handlers (`email_sender.py`): Manages sending of email and SMS notifications.

## Usage

### Starting the Servers

1. Start the RabbitMQ service on your machine or connect to a remote RabbitMQ instance.

2. Start the RabbitMQ consumer: python sender.py

3. Start the main FastAPI server

### API Endpoints

1. Send Notification
- Endpoint: `POST /notification/send`
- Payload example:
  ```json
  {
    "mobileNumber": "98xxxxxxx1",
    "remark1": "Transaction 1",
    "retrievalReferenceNumber": "701125451",
    "amount": "100",
    "merchantId": "99XXXXXXXXX1",
    "terminalId": "222202XXXXXXXX1",
    "type": "alert",
    "uniqueId": "202307201141001",
    "properties": {
      "txnDate": "2023-07-22 01:00:10",
      "secondaryMobileNumber": "9012325641",
      "email": "customer@example.com",
      "sessionSrlNo": "61",
      "commission": "2.50",
      "initiator": "98xxxxxxx1"
    }
  }
  ```

2. Get Transactions
- Endpoint: `POST /callback`
- Payload example:
  ```json
  {
    "merchant_id": "99XXXXXXXXX1",
    "terminal_id": "222202XXXXXXXX1"
  }
  ```

## Component Details

1. `main.py`: Main FastAPI server
- Handles API requests
- Implements Fonepay API client
- Manages request validation and error handling

2. `receiver.py`: RabbitMQ client
- Processes transactions asynchronously
- Triggers email and SMS notifications

3. `sender.py`: RabbitMQ consumer
- Listens for messages on the RabbitMQ queue
- Handles message processing and responses

4. `email_sender.py`: Notification handler
- Sends email notifications using SMTP
- Sends SMS notifications using Twilio

## Testing

1. Use Postman to send POST requests with appropriate Payloads to receive responses.

2. Monitor the console output of all running components to track the flow of each transaction.

3. Check the email inbox and phone number specified in the test transactions for notifications.

## Deployment

For production deployment:
1. Set up a production-grade WSGI server like Gunicorn to run the FastAPI application.
2. Use a process manager like Supervisor to manage the RabbitMQ consumer process.
3. Set up proper monitoring and logging solutions.
4. Ensure all sensitive information (API keys, passwords) are stored securely, preferably using environment variables.

## Troubleshooting

- If you encounter connection issues with RabbitMQ, ensure the service is running and the connection parameters are correct.
- For API-related issues, check the Fonepay API documentation and ensure your API key and secret are valid.
- If notifications are not being sent, verify the email and SMS configurations in `email_sender.py`.