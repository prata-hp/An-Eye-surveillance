import os

from twilio.rest import Client


client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN"),
)


def send_sms(message: str):
    client.messages.create(
        body=message,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        to=os.getenv("POLICE_PHONE_NUMBER"),
    )


def send_whatsapp(message: str):
    client.messages.create(
        body=message,
        from_="whatsapp:+14155238886",
        to=f"whatsapp:{os.getenv('POLICE_PHONE_NUMBER')}",
    )


def make_call(message: str):
    client.calls.create(
        twiml=f"""
        <Response>
            <Say voice="alice">
                {message}
            </Say>
        </Response>
        """,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        to=os.getenv("POLICE_PHONE_NUMBER"),
    )
