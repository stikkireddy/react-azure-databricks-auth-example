import base64
import hashlib
import json
import time
import uuid
from typing import Optional, Mapping
from urllib.parse import urlencode

import requests
from google.auth import jwt
from pydantic import BaseModel

from constants import CLIENT_ID, WORKSPACE_URL, SCOPES, CIPHER, REDIRECT_URI, CLIENT_SECRET, REFRESH_TOKEN_WITHIN_N_SECONDS


class TokenInfo(BaseModel):
    access_token: Optional[str]
    refresh_token: Optional[str]
    token_type: str
    scope: str
    expires_in: int

    def to_encrypted_string(self) -> str:
        """Encrypts the Pydantic model instance and returns a JSON string."""
        json_data = self.json()
        encrypted_data = CIPHER.encrypt(json_data.encode())
        return encrypted_data.decode()

    @classmethod
    def from_encrypted_string(cls, encrypted_str: str):
        """Decrypts the encrypted string and recreates the Pydantic model instance."""
        decrypted_data = CIPHER.decrypt(encrypted_str.encode()).decode()
        json_data = json.loads(decrypted_data)
        return cls(**json_data)

    def decoded_access_token(self) -> Mapping[str, str]:
        return jwt.decode(self.access_token, verify=False)

    def attempt_refresh(self):
        print("Attempting to refresh token")
        url = f"{WORKSPACE_URL}/oidc/v1/token"
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'scope': SCOPES,
            'refresh_token': self.refresh_token
        }
        data = requests.post(url, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=data)
        access = data.json()
        try:
            token_info = TokenInfo(**access)
            self.access_token = token_info.access_token
            self.expires_in = token_info.expires_in
            self.refresh_token = token_info.refresh_token
        except Exception as e:
            self.access_token = None
            self.refresh_token = None
        return access

    def is_token_about_to_expire(self):
        current_time = time.time()
        expiration_time = int(self.decoded_access_token().get("exp"))
        about_to_expire = expiration_time - current_time < REFRESH_TOKEN_WITHIN_N_SECONDS
        return about_to_expire


class AuthorizationCodeInput(BaseModel):
    code_verifier: str
    code_challenge: str

    @classmethod
    def generate(cls):
        uuid1 = uuid.uuid4()
        uuid_str1 = str(uuid1).upper()
        code_verifier = uuid_str1 + "-" + uuid_str1
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8')
        code_challenge = code_challenge.replace('=', '')
        return cls(code_verifier=code_verifier, code_challenge=code_challenge)

class AuthorizeUrlResponse(BaseModel):
    authorize_url: str

    @classmethod
    def from_authorize_payload(cls, payload: 'AuthorizePayload'):
        return cls(authorize_url=payload.authorize_url)

class OauthChallengeCfg(BaseModel):
    state: str
    code_verifier: str

    @staticmethod
    def get_cookie_name():
        return "oauth_challenge_cfg"

    @classmethod
    def from_cookie(cls, cookie: str):
        cookie_data = json.loads(cookie)
        return cls(**cookie_data)

class AuthorizePayload(BaseModel):
    authorize_url: str
    code_challenge: AuthorizationCodeInput
    state: str

    def to_oauth_cfg(self):
        return OauthChallengeCfg(state=self.state, code_verifier=self.code_challenge.code_verifier)

    @staticmethod
    def generate_authorization_code_url(client_id, redirect_url, state, code_challenge):
        base_url = f"{WORKSPACE_URL}/oidc/v1/authorize"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_url,
            "response_type": "code",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "scope": SCOPES
        }

        query_string = urlencode(params)

        return f"{base_url}?{query_string}"

    @classmethod
    def generate(cls):
        auth_code = AuthorizationCodeInput.generate()
        state = uuid.uuid4()
        auth_url = cls.generate_authorization_code_url(
            client_id=CLIENT_ID,
            redirect_url=REDIRECT_URI,
            state=state,
            code_challenge=auth_code.code_challenge
        )
        return cls(authorize_url=auth_url, code_challenge=auth_code, state=str(state))
