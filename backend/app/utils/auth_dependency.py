from fastapi import Header, HTTPException
from app.services.firebase_service import verify_firebase_token


async def get_current_firebase_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization token"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Use: Bearer <token>"
        )

    token = authorization.replace("Bearer ", "")

    try:
        decoded_token = verify_firebase_token(token)
        return decoded_token

    except ValueError as error:
        raise HTTPException(
            status_code=401,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Firebase token"
        )