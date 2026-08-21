"""Single place where the acting user is resolved.

The Phase 2 backend has no authentication layer: the React client keeps the
profile in localStorage and passes the user id explicitly. Rather than trusting
a body field in every handler, all adaptive routes resolve identity here, and
every adaptive query is filtered by the resolved id so one user can never read
another user's attempts, mastery, mistakes or recommendations.

When authentication is added, populate `request.state.user_id` in the auth
middleware — this function will prefer it over anything the client sends.
"""
from typing import Optional

from fastapi import HTTPException, Request


def resolve_user_id(request: Request, provided: Optional[str] = None) -> str:
    """Authenticated identity if available, else the client-supplied id."""
    authenticated = getattr(request.state, "user_id", None)
    if authenticated:
        if provided and provided != authenticated:
            raise HTTPException(status_code=403, detail="Cannot access another user's data")
        return authenticated

    header_user = request.headers.get("X-User-Id")
    if header_user and provided and header_user != provided:
        raise HTTPException(status_code=403, detail="Cannot access another user's data")

    user_id = provided or header_user
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    return user_id


def optional_user_id(request: Request, provided: Optional[str] = None) -> Optional[str]:
    """Same resolution, but anonymous callers are allowed (returns None)."""
    try:
        return resolve_user_id(request, provided)
    except HTTPException as exc:
        if exc.status_code == 400:
            return None
        raise
