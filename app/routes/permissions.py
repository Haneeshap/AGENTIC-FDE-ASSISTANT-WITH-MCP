from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any, List

from app.auth.permissions import check_permission, grant_permission, revoke_permission, list_permissions

router = APIRouter()


@router.post("/permissions")
async def grant_permission_endpoint(
    tenant_id: str,
    user_id: str,
    tool: str,
    action: str,
    expires_at: Optional[str] = None,
    granted_by: str = "admin",
):
    granted_by = "admin"

    grant_permission(tenant_id, user_id, tool, action, granted_by, expires_at)

    return {
        "granted": True,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "tool": tool,
        "action": action,
        "granted_by": granted_by,
    }


@router.delete("/permissions")
async def revoke_permission_endpoint(
    tenant_id: str,
    user_id: str,
    tool: str,
    action: str,
):
    count = revoke_permission(tenant_id, user_id, tool, action)

    return {"revoked": count > 0}


@router.get("/permissions")
async def list_permissions_endpoint(
    tenant_id: str,
    user_id: str,
):
    perms = list_permissions(tenant_id, user_id)
    return {"permissions": perms}