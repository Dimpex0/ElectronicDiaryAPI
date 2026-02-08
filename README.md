# Electronic Diary API

A FastAPI-based backend for a school electronic diary system. This API manages users (Students, Teachers, Parents, Principals), classes, subjects, grades, and file uploads.

---

## 🛠️ Prerequisites

* **Python 3.10+**
* **Virtual Environment** (recommended)

---

## 📦 Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/your-username/electronic-diary-api.git](https://github.com/your-username/electronic-diary-api.git)
    cd electronic-diary-api
    ```

2.  **Create and activate a virtual environment**
    * *Windows:*
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    * *macOS/Linux:*
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

---

## ⚙️ Configuration

Create a `.env` file in the root directory and add the following configuration.

```ini
# Security
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRATION_MINUTES=30

# File Uploads
MEDIA_PATH=media

# Email Configuration
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_FROM=your_email@example.com