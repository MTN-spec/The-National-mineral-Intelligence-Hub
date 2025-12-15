import time
import json
import random
import datetime

class APILogger:
    """Helper to store API logs for the Dev Console."""
    logs = []

    @classmethod
    def log(cls, service, method, url, payload, response_code, response_body):
        entry = {
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "service": service,
            "method": method,
            "url": url,
            "payload": payload,
            "status": response_code,
            "response": response_body
        }
        cls.logs.insert(0, entry) # Newest first

class SmsService:
    @staticmethod
    def send_sms(phone, message):
        """Simulate sending an SMS via a gateway like Twilio or Econet."""
        payload = {"to": phone, "body": message}
        # Simulate network latency
        time.sleep(0.5) 
        
        response = {"status": "success", "message_id": f"SM{random.randint(10000,99999)}"}
        APILogger.log("SMS_Gateway", "POST", "/v1/sms/send", payload, 200, response)
        return True

import smtplib
import ssl
from email.message import EmailMessage
import streamlit as st

class EmailService:
    @staticmethod
    def send_email(to_email, subject, body):
        """Sends a real email using Gmail SMTP and Streamlit secrets."""
        try:
            # 1. Get Credentials
            if "email" not in st.secrets:
                raise ValueError("Missing [email] section in .streamlit/secrets.toml")
            
            sender_email = st.secrets["email"]["address"]
            sender_password = st.secrets["email"]["password"] # App Password

            # 2. Construct Message
            msg = EmailMessage()
            msg.set_content(body)
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = to_email

            # 3. Connect to Gmail SMTP (SSL)
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            response = {"status": "sent", "timestamp": datetime.datetime.now().isoformat()}
            APILogger.log("SMTP_Server (Real)", "POST", "/mail/send", {"to": to_email, "subject": subject}, 200, response)
            return True

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            # Log the error but raise it so the UI knows
            APILogger.log("SMTP_Server", "ERROR", "/mail/send", {"error": str(e)}, 500, {})
            # We want to be strict, so we re-raise or return False
            raise e

class EcoCashGateway:
    @staticmethod
    def initiate_payment(amount, phone, reference):
        """
        Simulate the EcoCash Merchant Payment Flow.
        1. Merchant Request (API)
        2. Customer USSD Prompt (Simulated)
        3. Payment Result
        """
        endpoint = "https://api.ecocash.co.zw/v2/merchant/payment"
        payload = {
            "merchant_id": "ECO-12345",
            "amount": amount,
            "customer_phone": phone,
            "reference": reference,
            "currency": "USD"
        }
        
        # Simulate polling/USSD wait
        time.sleep(1.5)
        
        # Randomly succeed or fail (mostly succeed for demo)
        if random.random() > 0.1:
            response = {
                "transaction_id": f"TXN-{random.randint(100000, 999999)}",
                "status": "APPROVED",
                "message": "Payment successful."
            }
            code = 200
            success = True
        else:
             response = {
                "error_code": "E005",
                "status": "FAILED",
                "message": "Insufficient funds or User Cancelled."
            }
             code = 400
             success = False

        APILogger.log("EcoCash_API", "POST", endpoint, payload, code, response)
        return success, response
