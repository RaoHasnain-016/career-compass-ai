import json
import os
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv
from google.auth.exceptions import TransportError
from requests.exceptions import RequestException

load_dotenv()

if not firebase_admin._apps:
    credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

    if credentials_json:
        try:
            credentials_data = json.loads(credentials_json)
        except json.JSONDecodeError:
            raise ValueError(
                "FIREBASE_CREDENTIALS_JSON must contain valid service-account JSON."
            ) from None
        if not isinstance(credentials_data, dict):
            raise ValueError(
                "FIREBASE_CREDENTIALS_JSON must contain a service-account JSON object."
            )
        try:
            cred = credentials.Certificate(credentials_data)
        except (TypeError, ValueError):
            raise ValueError(
                "FIREBASE_CREDENTIALS_JSON contains invalid service-account credentials."
            ) from None
    elif credentials_path:
        cred = credentials.Certificate(credentials_path)
    else:
        raise ValueError(
            "Set FIREBASE_CREDENTIALS_JSON or FIREBASE_CREDENTIALS_PATH "
            "to configure Firebase Admin."
        )

    firebase_admin.initialize_app(cred)


class FirebaseVerificationUnavailableError(RuntimeError):
    """Firebase's verification certificates could not be retrieved."""


def verify_firebase_token(token: str):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except (auth.CertificateFetchError, TransportError, RequestException) as error:
        raise FirebaseVerificationUnavailableError(
            "Authentication service is temporarily unavailable. Please try again shortly."
        ) from error
    except Exception as error:
        raise ValueError(f"Invalid Firebase token: {str(error)}")
