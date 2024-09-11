# Koili Notification Middleware

## Introduction

The Koili Notification Middleware is a robust solution designed to handle transaction notifications for Fonepay, a digital payment platform. This system integrates with Fonepay's API to send notifications and retrieve transaction details, while also implementing asynchronous processing using RabbitMQ for improved scalability and reliability.

Key features include:
- RESTful API for sending notifications and retrieving transaction data
- Asynchronous processing of transactions using RabbitMQ
- Email and SMS notifications for successful transactions
- Integration with Koili IPN (Instant Payment Notification) system
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

## Getting Started

### Prerequisites

- Python 3.7+
- RabbitMQ server
- SMTP server access (for email notifications)
- Twilio account (for SMS notifications)
- MongoDB database

### Installation

1. Clone the repository: 
   ```
   git clone https://dev.azure.com/BitsKraft/Koili%20(IPN%20Platform)/_git/koili-notification-middleware
   ```

2. Run RabbitMQ on Docker:
   ```
   docker run -d --name rabbitmq --restart always -p 5672:5672 -p 15672:15672 rabbitmq:3.13.4-management
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Configuration

1. RabbitMQ Configuration:
   - Update the connection parameters in `.env`:
     ```
     RABBITMQ_SERVER=your_rabbitmq_server
     RABBITMQ_PORT=5672
     RABBITMQ_USER=your_username
     RABBITMQ_PASS=your_password
     ```

2. Fonepay API Configuration:
   - Update the API key and secret in `.env`:
     ```
     FONEPAY_API_SECRET=your_api_secret
     ```

3. Email Configuration:
   - Update the email settings in `.env`:
     ```
     USER=your_email@gmail.com
     PASSWORD=your_email_password
     ```

4. SMS Configuration:
   - Update the Twilio credentials in `.env`:
     ```
     TWILIO_ACCOUNT_SID=your_account_sid
     TWILIO_AUTH_TOKEN=your_auth_token
     TWILIO_PHONE_NUMBER=your_twilio_phone_number
     ```

5. MongoDB Configuration:
   - Update the MongoDB connection details in `.env`:
     ```
     DB_URL=your_mongodb_connection_string
     DB_NAME=your_database_name
     ```

6. Koili IPN Configuration:
   - Update the Koili IPN API endpoint and subscription key in `.env`:
     ```
     API_ENDPOINT=your_koili_ipn_api_endpoint
     Subscription-Key=your_subscription_key
     ```

## System Architecture

The system consists of several interconnected components:

1. FastAPI Server (`main.py`): Handles incoming API requests, interacts with the Fonepay API, and enqueues transactions for processing.
2. RabbitMQ Consumer (`sender.py`): Consumes messages from the queues and processes them in batches.
3. RabbitMQ Producer (`receiver.py`): Publishes messages to appropriate queues based on enabled services.
4. Notification Handlers (`email_sender.py`): Manages sending of email and SMS notifications.
5. Koili IPN Integration (`koili_ipn.py`): Sends Instant Payment Notifications to the Koili system.

## Usage

### Starting the Servers

1. Start the RabbitMQ service on your machine or connect to a remote RabbitMQ instance.

2. Start the RabbitMQ consumer:
   ```
   python sender.py
   ```

3. Start the main FastAPI server:
   ```
   uvicorn main:app --reload
   ```

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
       "merchantId": "99XXXXXXXXX1",
       "terminalId": "222202XXXXXXXX1"
     }
     ```

## Component Details

1. `main.py`: Main FastAPI server
   - Handles API requests
   - Implements Fonepay API client
   - Manages request validation and error handling

2. `receiver.py`: RabbitMQ message producer
   - Publishes messages to appropriate queues based on enabled services
   - Starts consumers for enabled queues

3. `sender.py`: RabbitMQ consumer
   - Processes messages from queues in batches
   - Triggers email, SMS, and Koili IPN notifications

4. `email_sender.py`: Notification handler
   - Sends email notifications using SMTP
   - Sends SMS notifications using Twilio

5. `koili_ipn.py`: Koili IPN integration
   - Sends Instant Payment Notifications to the Koili system

## Testing

1. Use Postman or cURL to send POST requests to the API endpoints with appropriate payloads.

2. Monitor the console output of all running components to track the flow of each transaction.

3. Check the email inbox and phone number specified in the test transactions for notifications.

4. Verify that Koili IPN notifications are being sent correctly.

## Deployment

For production deployment:
1. Set up a production-grade WSGI server like Gunicorn to run the FastAPI application.
2. Use a process manager like Supervisor to manage the RabbitMQ consumer processes.
3. Set up proper monitoring and logging solutions.
4. Ensure all sensitive information (API keys, passwords) are stored securely, preferably using environment variables or a secure key management system.
5. Configure SSL/TLS for secure communication between components.

## Troubleshooting

- If you encounter connection issues with RabbitMQ, ensure the service is running and the connection parameters are correct.
- For API-related issues, check the Fonepay API documentation and ensure your API key and secret are valid.
- If notifications are not being sent, verify the email and SMS configurations in `email_sender.py`.
- Check the logs for any error messages or unexpected behavior.
- Ensure that the Koili IPN integration is configured correctly and the API endpoint is accessible.

more to be processed