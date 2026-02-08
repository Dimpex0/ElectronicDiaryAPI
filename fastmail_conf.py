import os
from typing import List

from fastapi_mail import ConnectionConfig, FastMail
from pydantic import BaseModel, EmailStr, SecretStr

MAIL_USERNAME = os.getenv("MAIL_USERNAME", "username")
MAIL_FROM = os.getenv("MAIL_FROM", "from@from.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "password")

email_conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,  # type: ignore[arg-type]
    MAIL_FROM=MAIL_FROM,  # type: ignore[arg-type]
    MAIL_PASSWORD=MAIL_PASSWORD,  # type: ignore[arg-type]
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

class EmailSchema(BaseModel):
    email: List[EmailStr]

fm = FastMail(email_conf)
