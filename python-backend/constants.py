import os
import secrets

from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.environ.get("DATABRICKS_ACCOUNT_ID")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")
WORKSPACE_URL = os.environ.get("WORKSPACE_URL").rstrip("/")
REACT_SERVICE_URL = os.environ.get("REACT_SERVICE_URL").rstrip("/")
REFRESH_TOKEN_WITHIN_N_SECONDS = int(os.environ.get("REFRESH_TOKEN_WITHIN_N_SECONDS_BEFORE_EXPIRY", "300"))
SCOPES = ["all-apis", "offline_access"]

# use this in another file if you need to generate the key
# secrets.token_urlsafe(32)
COOKIE_ENCRYPTION_KEY = os.environ.get("COOKIE_ENCRYPTION_KEY", secrets.token_urlsafe(32))
PORT = int(os.environ.get("PORT", "5173"))
HOST = os.environ.get("HOST", "localhost")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")  # development, production
IS_DEVELOPMENT = ENVIRONMENT == "development"
COOKIE_MAX_AGE = int(os.environ.get("COOKIE_MAX_AGE_SECONDS", "3600"))
