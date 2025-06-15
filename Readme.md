# 🔐 Secure File Storage System

A web-based application that allows users to securely upload, encrypt, store, decrypt, download, and delete their files. It uses **OTP-based email verification**, **symmetric encryption with Fernet**, and a **MySQL database** for user and file management.

---

## 🚀 Features

- ✅ User login with OTP sent via email (Two-Factor Authentication)
- 🔒 File encryption using Fernet symmetric key encryption
- ☁️ Encrypted file storage on the server
- 🔑 User-provided decryption key for downloading files
- 🧼 File deletion option with confirmation prompt
- 🎨 Responsive and modern UI with custom background

---

## 🛠️ Technologies Used

| Component       | Technology            |
|----------------|------------------------|
| Backend         | Python, Flask         |
| Frontend        | HTML, CSS             |
| Encryption      | `cryptography` library (Fernet) |
| Email OTP       | `flask-mail`, `pyotp` |
| Database        | MySQL (via `mysql-connector-python`) |
| Deployment      | `flask`               |

---

## 📦 Project Structure

secure-file-storage/
│
├── uploads/ # Encrypted file storage
├── static/ # Static files (background images etc.)
│ └── background.jpg
├── templates/ # HTML templates
│ ├── login.html
│ ├── otp.html
│ ├── upload.html
│ └── dashboard.html
├── config.py # Configuration file for DB and Mail
├── app.py # Main Flask application
└── README.md # This file


# ⚙️ How the Secure File Storage System Works

## 🧩 1. User Authentication via OTP

- The user visits the homepage and enters their **email address**.
- If the user is new:
  - A new record is created in the database.
  - A **new OTP secret** is generated using `pyotp`.
- If the user already exists:
  - Their existing secret is fetched.
- A **Time-based One-Time Password (TOTP)** is generated and sent to the user via email using `Flask-Mail`.
- The user enters the OTP on the verification page.
- The OTP is verified using the shared secret (`TOTP.verify()`), allowing access to the dashboard.

---

Once the user logs in via OTP verification, they are redirected to the **Dashboard**. From there, the Secure File Storage System offers a secure and simple interface for managing files. Here's the complete workflow:

---

## ✅ Step-by-Step Dashboard Workflow

### 1️⃣ Redirect to Dashboard

- After successful OTP verification, the user is redirected to:
- The dashboard fetches and displays all files previously uploaded by the logged-in user.
- Each file is shown in a table with:
- **Filename**
- **Input field** for decryption key
- **Download & Decrypt** button
- **Delete** button

---

### 2️⃣ Uploading a New File

- User can click on **"Upload More Files"** which redirects to:

- On upload:
- A unique **Fernet key** is generated.
- The file is **encrypted** using this key.
- Encrypted file is saved in the `uploads/` folder.
- The file metadata is saved in the database.
- The encryption key is shown on the screen once — the user must save it securely.

> ⚠️ The decryption key is not stored in the system.

---

### 3️⃣ Download & Decrypt a File

- Back on the dashboard, the user sees their file list.
- To retrieve a file:
- The user enters the **previously saved decryption key**.
- Clicks **"Download & Decrypt"**.
- Backend process:
- Retrieves the encrypted file.
- Attempts decryption using the provided key.
- If successful, creates a temporary decrypted file and sends it as a download.
- Deletes the temporary file after download.

> ❗ If the key is incorrect, decryption fails and an error message is shown.

---

### 4️⃣ Deleting a File

- User can click the **"Delete"** button beside any file.
- Confirmation prompt appears before deletion.
- If confirmed:
- The file is removed from disk (`/uploads/`).
- Corresponding record is deleted from the database.

---

### 5️⃣ Logout

- Clicking **"Logout"** returns the user to the login page and clears the session.

---

## 💡 Summary Flow

```plaintext
Login (Email & OTP) → Dashboard
  ├── Upload → Encrypt → Show Key → Store File
  ├── Download → Enter Key → Decrypt → Send File
  ├── Delete → Remove File from Disk & DB
  └── Logout → End Session
