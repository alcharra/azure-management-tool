# IMPORT STANDARD LIBRARY MODULES
# ///////////////////////////////////////////////////////////////
import time
from typing import Optional, Dict, Any, Tuple

# IMPORT THIRD-PARTY PACKAGES
# ///////////////////////////////////////////////////////////////
import jwt

# IMPORT AZURE PACKAGES
# ///////////////////////////////////////////////////////////////
from azure.identity import InteractiveBrowserCredential

# AUTHENTICATION CLASS
# ///////////////////////////////////////////////////////////////
class AuthenticationManager:

    def __init__(self) -> None:
        self.token: Optional[str] = None
        self.expires_on: float = 0.0
        self.payload: Optional[Dict[str, Any]] = None

    # GET TOKEN
    # ///////////////////////////////////////////////////////////////
    def get_token(self) -> Tuple[str, Optional[str]]:
        if self.token and time.time() < self.expires_on:
            return self.token, self.get_user_name_from_token()
        else:
            credential = InteractiveBrowserCredential()
            token = credential.get_token("https://management.azure.com/.default")
            self.token = token.token
            self.expires_on = time.time() + (token.expires_on - time.time())
            return self.token, self.get_user_name_from_token()

    # DECODE TOKEN
    # ///////////////////////////////////////////////////////////////
    def decode_token(self) -> Optional[Dict[str, Any]]:
        try:
            self.payload = jwt.decode(self.token, options={"verify_signature": False}, algorithms=["RS256"])
            return self.payload
        except jwt.DecodeError as e:
            print(f"Failed to decode token: {e}")
            return None

    # GET USER NAME FROM TOKEN
    # ///////////////////////////////////////////////////////////////
    def get_user_name_from_token(self) -> Optional[str]:
        self.decode_token()
        if self.payload:
            return self.payload.get('name') or self.payload.get('upn')
        else:
            print("Could not extract user information from token.")
            return None