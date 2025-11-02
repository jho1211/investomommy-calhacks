from config import JWKS_URL
from jose import jwt, JWTError, jwk
from jose.utils import base64url_decode
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cachetools import TTLCache
import requests
import time

security = HTTPBearer()
cache = TTLCache(maxsize=1, ttl=3600)

def get_jwks():
    """Fetch cached JWKS and return it"""
    if JWKS_URL not in cache:
        response = requests.get(JWKS_URL)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch JWKS")
        cache[JWKS_URL] = response.json()
    return cache[JWKS_URL]

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token from Authorization header"""
    token = credentials.credentials
    jwks = get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header["kid"]
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if key is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        public_key = jwk.construct(key, algorithm="ES256")
        
        message, encoded_sig = token.rsplit('.', 1)
        decoded_sig = base64url_decode(encoded_sig.encode())
        if not public_key.verify(message.encode(), decoded_sig):
            raise HTTPException(status_code=401, detail="Invalid signature")
        payload = jwt.get_unverified_claims(token)

        if payload.get("exp") and payload["exp"] <= time.time():
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Failed to verify token: {str(e)}")