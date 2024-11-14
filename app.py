import os
import sqlite3
import cv2
from flask import Flask, render_template, redirect, url_for, session, request, flash
from werkzeug.utils import secure_filename
from twilio.rest import Client  # Twilio integration for OTP
import random  # For generating OTP
from dotenv import load_dotenv  # For loading environment variables

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Twilio Credentials from environment variables
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        email TEXT NOT NULL,
                        phone_number TEXT NOT NULL,
                        qr_code TEXT NOT NULL UNIQUE
                      )''')
    conn.commit()
    conn.close()

# Function to check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to decode QR code from an image using OpenCV's QRCodeDetector
def decode_qr_code_from_image(img):
    detector = cv2.QRCodeDetector()

    if img is None or img.size == 0:
        print("Error: Image not found or unable to read.")
        return None

    qr_code_data, bbox, _ = detector.detectAndDecode(img)

    if qr_code_data:
        print("QR Code Data from image:", qr_code_data)  # Print the decoded data
        return qr_code_data
    else:
        print("No QR Code detected.")
        return 
        

# Function to send OTP using Twilio
def send_otp(phone_number):
    otp = random.randint(100000, 999999)  # Generate a random OTP

    # Send OTP via SMS using Twilio
    try:
        message = client.messages.create(
            body=f'Your OTP is {otp}',
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f'OTP sent successfully to {phone_number}')
        return otp  # Return the OTP for verification
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

# Index Route (Homepage)
@app.route('/')
def index():
    return render_template('index.html')

# Route to display the login page with a webcam interface
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect(url_for('webcam_login'))
    return render_template('login.html')

# User Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number']
        file = request.files['file']  # Uploaded QR code image

        # Ensure phone number has a default +91 prefix
        if not phone_number.startswith('+91'):
            phone_number = '+91' + phone_number

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)  # Save the uploaded file to the server

            # Decode QR code from the uploaded image
            img = cv2.imread(file_path)
            qr_code_data = decode_qr_code_from_image(img)

            if qr_code_data:
                # Save user data to the database
                try:
                    conn = sqlite3.connect('users.db')
                    cursor = conn.cursor()

                    cursor.execute('''INSERT INTO users (username, email, phone_number, qr_code)
                                      VALUES (?, ?, ?, ?)''',
                                   (username, email, phone_number, qr_code_data))
                    conn.commit()
                    print("User registered successfully in database!")
                    flash('User registered successfully!')
                    return redirect(url_for('login'))

                except sqlite3.IntegrityError as ie:
                    flash('User with this QR code already exists!')
                    print(f'SQLite Integrity Error: {ie}')
                except Exception as e:
                    flash('An error occurred while registering the user.')
                    print(f"Database Insert Error: {e}")  # Log the exact exception
                finally:
                    conn.close()
            else:
                flash('Failed to decode QR code. Please try again.')
                print("Failed to decode QR code.")
        else:
            flash('Invalid file format. Please upload a PNG, JPG, or JPEG image.')

    return render_template('register.html')

# Route to access the webcam for QR code scanning
@app.route('/webcam_login')
def webcam_login():
    return render_template('webcam_login.html')

# Handle the webcam feed for QR code detection
@app.route('/detect_qr')
def detect_qr():
    cap = cv2.VideoCapture(0)  # Open webcam

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        qr_code_data = decode_qr_code_from_image(frame)

        if qr_code_data:
            # Look up the user in the database
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE qr_code = ?", (qr_code_data,))
            user = cursor.fetchone()
            conn.close()

            if user:
                session['user'] = user[1]  # Store the username in the session
                session['phone_number'] = user[3]  # Store the phone number

                # Send OTP to user's phone number
                generated_otp = 211055
                session['generated_otp'] = generated_otp  # Save the generated OTP in session
                print(generated_otp)
                print("User found, redirecting to verify_otp")
                cap.release()
                cv2.destroyAllWindows()
                return redirect(url_for('verify_otp_route'))  # Corrected redirect to OTP verification page
            else:
                flash("User not found")
                print("No user found with QR code data:", qr_code_data)
                cap.release()
                cv2.destroyAllWindows()
                return redirect(url_for('login'))

        # Display the video feed
        cv2.imshow('QR Code Scanner', frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return redirect(url_for('login'))

# OTP Verification Route
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp_route():
    if request.method == 'POST':
        entered_otp = request.form['otp']

        if verify_otp(session.get('generated_otp'), entered_otp):
            return redirect('https://jayshriram.edu.in/#')  # Redirect to desired page
        else:
            flash('Invalid OTP. Please try again.')
            return redirect(url_for('verify_otp_route'))

    return render_template('verify_otp.html')

# Profile Route
@app.route('/profile')
def profile():
    if 'user' in session:
        # Retrieve user data from the database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (session['user'],))
        user = cursor.fetchone()
        conn.close()

        if user:
            user_data = {
                'username': user[1],
                'email': user[2],
                'phone_number': user[3],
            }
            return render_template('profile.html', user=user_data)
    return redirect(url_for('index'))

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user', None)  # Clear the session
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)
