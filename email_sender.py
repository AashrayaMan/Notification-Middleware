import smtplib
from email.message import EmailMessage
from twilio.rest import Client
import logging
from twilio.base.exceptions import TwilioRestException

# Configure root logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set Twilio logger to ERROR level
logging.getLogger('twilio').setLevel(logging.ERROR)

def sms_alert(body, to):
    account_sid = 'AC65ff0f2cfe0f7a5e1eb253576aa15bcd'
    auth_token = '03b508b034332d3ba9074805b1504674'
    client = Client(account_sid, auth_token)

    try:
        message = client.messages.create(
            from_='+12075038547',
            body=body,
            to=to
        )
        logger.info(f"SMS sent successfully. SID: {message.sid}")
    except TwilioRestException as e:
        logger.error(f"Twilio API error: {e.msg}")
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")

def email_alert(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)

    msg['subject'] = subject
    msg['to'] = to

    user = "koiliteam1@gmail.com"
    msg['from'] = user
    password = "yseg vcyp dlbx ewsy"

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
        logger.info(f"Email Sent")
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication failed. Check your email and password.")
    except smtplib.SMTPException as e:
        logger.error(f"An error occurred while sending the email: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
    finally:
        try:
            server.quit()
        except:
            pass

def send_notifications(subject, body, email_to, sms_to):
    email_alert(subject, body, email_to)
    sms_alert(body, sms_to)
