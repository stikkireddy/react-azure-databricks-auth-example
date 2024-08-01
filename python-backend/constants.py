import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.environ.get("DATABRICKS_ACCOUNT_ID")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")
WORKSPACE_URL = os.environ.get("WORKSPACE_URL").rstrip("/")
REACT_SERVICE_URL = os.environ.get("REACT_SERVICE_URL").rstrip("/")
REFRESH_TOKEN_WITHIN_N_SECONDS = int(os.environ.get("REFRESH_TOKEN_WITHIN_N_SECONDS_BEFORE_EXPIRY", "300"))
SCOPES = "all-apis offline_access"

# use this in another file if you need to generate the key
# def generate_key():
#     return Fernet.generate_key()
COOKIE_ENCRYPTION_KEY = os.environ.get("COOKIE_ENCRYPTION_KEY").encode("utf-8")
CIPHER = Fernet(COOKIE_ENCRYPTION_KEY)
PORT = int(os.environ.get("PORT", "5173"))
HOST = os.environ.get("HOST", "localhost")