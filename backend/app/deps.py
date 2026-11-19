"""Request dependencies.

Authentication is SIMULATED for the hackathon: the client sends `X-Demo-User: <user id>`.
Phase 2 replaces this with secure session auth (PRD §17.1) behind the same dependencies.
"""
from collections.abc import Callable

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .models import User

STAFF_ROLES = {"verifier", "senior_reviewer", "admin"}


def current_user_optional(
    x_demo_user: str | None = Header(default=None), db: Session = Depends(get_db)
) -> User | None:
    if not x_demo_user:
        return None
    try:
        user = db.get(User, int(x_demo_user))
    except ValueError:
        user = None
    if user is None or user.account_status != "active":
        raise HTTPException(401, "Unknown or inactive demo user")
    return user


def current_user(user: User | None = Depends(current_user_optional)) -> User:
    if user is None:
        raise HTTPException(401, "Sign in (choose a demo user) to continue")
    return user


def require_roles(*roles: str) -> Callable[..., User]:
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Your role does not allow this action")
        return user
    return dep
