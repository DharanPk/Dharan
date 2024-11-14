import os
from twilio.rest import Client
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Function to send the OTP
def send_otp(phone_number):
    # Generate a random 6-digit OTP
    otp = random.randint(100000, 999999)

    # Send OTP via SMS using Twilio
    try:
        message = client.messages.create(
            body=f'Your OTP is {otp}',
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f'OTP sent successfully to {phone_number}')
        return otp  # Return the generated OTP for verification
    except Exception as e:
        print(f'Failed to send OTP: {e}')
        return None

# Function to verify the OTP entered by the user
def verify_otp(generated_otp, entered_otp):
    if str(generated_otp) == str(entered_otp):
        print("OTP verified successfully!")
        return True
    else:
        print("Invalid OTP. Please try again.")
        return False

if __name__ == '__main__':
    # Input phone number in E.164 format (e.g., +1234567890)
    phone_number = input('Enter the phone number (in E.164 format): ')

    # Send OTP and get the generated one
    generated_otp = send_otp(phone_number)

    if generated_otp:
        # Ask the user to enter the OTP they received
        entered_otp = input('Enter the OTP you received: ')

        # Verify the OTP
        is_verified = verify_otp(generated_otp, entered_otp)

        if is_verified:
            print("Access granted. Redirecting to the website...")
            # Redirect or grant access (you can integrate redirection here if using a web app)
        else:
            print("Access denied.")
