from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to SQLite Database to store user information
def connect_db():
    conn = sqlite3.connect('users.db')
    return conn

# Create user table if it doesn't exist
def init_db():
    conn = connect_db()
    with conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            profile TEXT NOT NULL)''')
    conn.close()

# Index Route (Homepage)
@app.route('/')
def index():
    return render_template('index.html')

# Login Route
@app.route('/login', methods=['POST'])
def login():
    qr_code_data = request.form.get('qr_code_data')  # Extract QR code data (user identifier)
    
    conn = connect_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (qr_code_data,)).fetchone()
    
    if user:
        session['user'] = user[1]  # Store the user profile in session
        return redirect(url_for('profile'))
    else:
        return "User not found", 404

# Profile Route
@app.route('/profile')
def profile():
    if 'user' in session:
        user_profile = session['user']
        return f"Welcome, {user_profile}! You are logged in."
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)
