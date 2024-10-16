import time
import jwt
from azure.identity import InteractiveBrowserCredential

class AuthenticationManager:

    def __init__(self):
        self.token = None
        self.expires_on = 0

    def get_token(self):
        if self.token and time.time() < self.expires_on:
            # Return cached token if valid
            return self.token
        else:
            # Authenticate and fetch a new token
            credential = InteractiveBrowserCredential()
            token = credential.get_token("https://management.azure.com/.default")
            # Cache the token and expiration time
            self.token = token.token
            self.expires_on = time.time() + (token.expires_on - time.time())
            return self.token
        
    def decode_token(self):
        token = self.get_token()
        try:
            payload = jwt.decode(token, options={"verify_signature": False}, algorithms=["RS256"])
            return payload
        except jwt.DecodeError as e:
            print(f"Failed to decode token: {e}")
            return None
        
    def get_user_name_from_token(self):
        payload = self.decode_token()
        if payload:
            return payload.get("name") or payload.get("preferred_username")
        else:
            print("Could not extract user information from token.")
            return None