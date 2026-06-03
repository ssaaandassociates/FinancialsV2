"""
Authentication & tenancy — SaaS migration (Slice 0b).

Detects the JWT algorithm from the token header and verifies accordingly:
  - ES256/RS256 -> fetch the public key from the project's JWKS endpoint.
  - HS256        -> verify with the Legacy JWT secret (SUPABASE_JWT_SECRET).
"""
from typing import Optional
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
import jwt
from jwt import PyJWKClient

from app.config import SUPABASE_JWT_SECRET, SUPABASE_URL, AUTH_ENABLED
from app.database import get_db
from app.models.tenancy import Firm, User


class AuthError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=401, detail=detail)


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


_jwks_client: Optional[PyJWKClient] = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        if not SUPABASE_URL:
            raise AuthError("SUPABASE_URL not configured for asymmetric token verification.")
        jwks_url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


def verify_token(token: str) -> dict:
    """
    Verify a Supabase JWT and return its claims, handling both the new
    asymmetric (ES256/RS256) tokens and legacy symmetric (HS256) tokens.
    """
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "")

        if alg in ("ES256", "RS256"):
            signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                audience="authenticated",
                options={"verify_aud": True},
            )
        else:
            if not SUPABASE_JWT_SECRET:
                raise AuthError("Server missing SUPABASE_JWT_SECRET for HS256 verification.")
            claims = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_aud": True},
            )
        return claims
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired — please log in again.")
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Invalid token: {e}")
    except AuthError:
        raise
    except Exception as e:
        raise AuthError(f"Token verification failed: {e}")


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not AUTH_ENABLED:
        return None

    token = _extract_bearer(authorization)
    if not token:
        raise AuthError("Missing Authorization bearer token.")

    claims = verify_token(token)
    uid = claims.get("sub")
    email = claims.get("email") or claims.get("user_metadata", {}).get("email")
    if not uid:
        raise AuthError("Token missing subject (user id).")

    user = db.query(User).filter(User.id == uid).first()
    if user is None:
        firm = Firm(
            name=(email.split("@")[0] if email else "My Firm"),
            primary_email=email,
        )
        db.add(firm)
        db.flush()
        user = User(id=uid, email=email or f"{uid}@unknown", firm_id=firm.id)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if user.firm_id is None:
            firm = Firm(name=(email.split("@")[0] if email else "My Firm"),
                        primary_email=email)
            db.add(firm)
            db.flush()
            user.firm_id = firm.id
            db.commit()
            db.refresh(user)

    return user


def get_current_firm_id(
    user: Optional[User] = Depends(get_current_user),
) -> Optional[int]:
    if not AUTH_ENABLED:
        return None
    if user is None or user.firm_id is None:
        raise AuthError("No firm associated with this user.")
    return user.firm_id