import smtplib
from email.message import EmailMessage
from twilio.rest import Client

def sms_alert():
  account_sid = 'AC65ff0f2cfe0f7a5e1eb253576aa15bcd'
  auth_token = '03b508b034332d3ba9074805b1504674'
  client = Client(account_sid, auth_token)

  message = client.messages.create(
  from_='+12075038547',
  body='Message from Koili',
  to='+9779767661398'
  )

  print(message.sid)


def email_alert(subject,body,to):
    msg = EmailMessage()
    msg.set_content(body)

    msg['subject'] = subject
    msg['to'] = to

    user = "koiliteam1@gmail.com"
    msg['from'] = user
    password = "yseg vcyp dlbx ewsy"

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(user,password)
    server.send_message(msg)
    print("Email Sent")
    server.quit()

