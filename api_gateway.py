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

class EmailService:
    @staticmethod
    def send_email(to_email, subject, body):
        """Simulate sending an email."""
        payload = {"to": to_email, "subject": subject, "body": body}
        time.sleep(0.8)
        
        response = {"status": "sent", "timestamp": datetime.datetime.now().isoformat()}
        APILogger.log("SMTP_Server", "POST", "/mail/send", payload, 202, response)
        return True

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
