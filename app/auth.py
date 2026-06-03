"""
Authentication & tenancy — SaaS migration (Slice 0b).

Flow:
  1. Frontend logs in via Supabase Auth, receives a JWT (access token).
  2. Frontend sends it as `Authorization: Bearer <token>` on every API call.
  3. verify_token() decodes & validates the JWT using the Supabase Legacy JWT secret.
  4. get_current_user() resolves (or auto-creates) the local User row + their Firm.
  5. get_current_firm_id() returns the firm_id used to scope every data query.

Safety design:
  - If AUTH_ENABLED is False (no SUPABASE_JWT_SECRET set), the app stays in legacy
    single-tenant mode: get_current_firm_id() returns None and queries are unscoped,
    exactly like before. This lets the current deploy keep working until the secret
    is set and the frontend sends tokens. Zero breakage during rollout.
"""
from typing import Optional
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
import jwt

from app.config import SUPABASE_JWT_SECRET, AUTH_ENABLED
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


def verify_token(token: str) -> dict:
    """
    Verify a Supabase JWT (HS256 legacy secret) and return its claims.
    Supabase tokens carry: sub (user uuid), email, aud='authenticated', exp, etc.
    """
    try:
        claims = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256", "ES256", "RS256"],,
            audience="authenticated",
            options={"verify_aud": True},
        )
        return claims
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired — please log in again.")
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Invalid token: {e}")


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Resolve the logged-in user from the Supabase token.
    Auto-provisions a User + a personal Firm on first login.
    Returns None when AUTH_ENABLED is False (legacy mode).
    """
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
        # First login → create user + a personal firm (one firm per user)
        firm = Firm(
            name=(email.split("@")[0] if email else "My Firm"),
            primary_email=email,
        )
        db.add(firm)
        db.flush()  # get firm.id
        user = User(id=uid, email=email or f"{uid}@unknown", firm_id=firm.id)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Existing user with no firm (edge case) → attach one
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
    """
    The firm_id used to scope all data queries.
    Returns None in legacy mode (AUTH_ENABLED False) → queries stay unscoped.
    """
    if not AUTH_ENABLED:
        return None
    if user is None or user.firm_id is None:
        raise AuthError("No firm associated with this user.")
    return user.firm_id
