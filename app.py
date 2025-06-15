from flask import Flask, render_template, request, redirect, session, send_file, flash, url_for
from flask_mail import Mail, Message
import pyotp
import os
from cryptography.fernet import Fernet
import mysql.connector
from config import *


app = Flask(__name__, static_folder='static')

app.secret_key = os.urandom(24)

# Email config
app.config.from_object('config')
mail = Mail(app)

# MySQL connection
db = mysql.connector.connect(
    host=DB_HOST,
    port=3307,           
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = db.cursor(dictionary=True)

# Upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if user:
            secret = user['otp_secret']
        else:
            secret = pyotp.random_base32()
            cursor.execute("INSERT INTO users (email, otp_secret) VALUES (%s, %s)", (email, secret))
            db.commit()

        session['email'] = email
        session['secret'] = secret

        otp = pyotp.TOTP(secret).now()

        msg = Message("Your OTP Code", sender=MAIL_USERNAME, recipients=[email])
        msg.body = f"Your OTP is: {otp}"
        mail.send(msg)

        return redirect("/verify")
    return render_template("login.html")

@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        otp_input = request.form['otp']
        secret = session.get('secret')
        totp = pyotp.TOTP(secret)
        if totp.verify(otp_input, valid_window=1):
            return redirect("/dashboard")
        return "Invalid OTP"
    return render_template("otp.html")

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if not session.get('email'):
        return redirect("/")
    
    if request.method == "POST":
        file = request.files['file']
        email = session['email']

        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        user_id = user['id']

        key = Fernet.generate_key()
        fernet = Fernet(key)

        raw = file.read()
        encrypted = fernet.encrypt(raw)

        encrypted_filename = f"enc_{file.filename}"
        path = os.path.join(UPLOAD_FOLDER, encrypted_filename)
        with open(path, 'wb') as f:
            f.write(encrypted)

        cursor.execute(
            "INSERT INTO files (user_id, filename, filepath) VALUES (%s, %s, %s)", 
            (user_id, file.filename, path)
        )
        db.commit()

        return f"Uploaded & encrypted successfully!  Save this decryption key: <br><b>{key.decode()}</b>"

    return render_template("upload.html")

@app.route("/dashboard", methods=["GET"])
def dashboard():
    if not session.get('email'):
        return redirect("/")

    email = session['email']
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    if not user:
        return "User not found", 404
    user_id = user['id']

    cursor.execute("SELECT filename FROM files WHERE user_id=%s", (user_id,))
    files = cursor.fetchall()

    return render_template("dashboard.html", files=files)
@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    if not session.get('email'):
        return redirect("/")

    email = session['email']
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    if not user:
        flash("User not found!")
        return redirect(url_for('dashboard'))
    
    user_id = user['id']

   
    cursor.execute("SELECT filepath FROM files WHERE filename=%s AND user_id=%s", (filename, user_id))
    file = cursor.fetchone()

    if file:
        try:
            
            if os.path.exists(file['filepath']):
                os.remove(file['filepath'])

            # Delete from database
            cursor.execute("DELETE FROM files WHERE filename=%s AND user_id=%s", (filename, user_id))
            db.commit()

            flash("File deleted successfully.")
        except Exception as e:
            flash(f"Failed to delete file: {str(e)}")
    else:
        flash("File not found or permission denied.")

    return redirect(url_for('dashboard'))


@app.route("/download/<filename>", methods=["POST"])
def download(filename):
    if not session.get('email'):
        return redirect("/")

    key = request.form.get('key')
    if not key:
        flash("Decryption key is required!")
        return redirect(url_for('dashboard'))

    key = key.encode()

    cursor.execute("SELECT filepath FROM files WHERE filename=%s", (filename,))
    result = cursor.fetchone()
    if result:
        try:
            with open(result['filepath'], 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = Fernet(key).decrypt(encrypted_data)

            temp_path = f"temp_{filename}"
            with open(temp_path, 'wb') as f:
                f.write(decrypted_data)

            response = send_file(temp_path, as_attachment=True)

            @response.call_on_close
            def cleanup():
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            return response
        except Exception as e:
            flash(f"Decryption failed: {str(e)}")
            return redirect(url_for('dashboard'))

    flash("File not found!")
    return redirect(url_for('dashboard'))


if __name__ == "__main__":
    app.run(debug=True)
