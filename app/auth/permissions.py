import uuid
from datetime import datetime, timezone


_permissions_db: dict = {}


def check_permission(tenant_id: str, user_id: str, tool: str, action: str) -> bool:
    perm_key = f"{tenant_id}:{user_id}:{tool}:{action}"
    if perm_key in _permissions_db:
        perm = _permissions_db[perm_key]
        if perm.get("expires_at"):
            expires = datetime.fromisoformat(perm["expires_at"])
            now = datetime.now(timezone.utc)
            if now > expires:
                return False
        return True
    return False


def grant_permission(tenant_id: str, user_id: str, tool: str, action: str, granted_by: str, expires_at=None) -> bool:
    perm_key = f"{tenant_id}:{user_id}:{tool}:{action}"
    _permissions_db[perm_key] = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "user_id": user_id,
        "tool": tool,
        "action": action,
        "granted_by": granted_by,
        "granted_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at.isoformat() if expires_at else None,
    }
    return True


def revoke_permission(tenant_id: str, user_id: str, tool: str, action: str) -> int:
    perm_key = f"{tenant_id}:{user_id}:{tool}:{action}"
    if perm_key in _permissions_db:
        del _permissions_db[perm_key]
        return 1
    return 0


def list_permissions(tenant_id: str, user_id: str):
    result = []
    for perm_key, perm in _permissions_db.items():
        if perm["tenant_id"] == tenant_id and perm["user_id"] == user_id:
            result.append(perm)
    return result