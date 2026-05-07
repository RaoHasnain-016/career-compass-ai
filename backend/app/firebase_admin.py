import os
import firebase_admin
from firebase_admin import credentials, auth

_app = None

def init_firebase():
    global _app
    if _app:
        return _app
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-service-account.json")
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        _app = firebase_admin.initialize_app(cred)
    return _app

def verify_firebase_token(token: str):
    init_firebase()
    return auth.verify_id_token(token)
