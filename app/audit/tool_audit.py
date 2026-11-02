import uuid
from datetime import datetime, timezone
import json

# In-memory storage for tool audit (would be database-backed in production)
_tool_audit_db: list = []


def log_tool_call(tenant_id: str, user_id: str, tool: str, action: str, input: dict, output: dict,
                  latency_ms: int, status: str, trace_id: str, correlation_id: str,
                  error_message: str = None) -> str:
    """
    Log a tool call to the audit table.
    
    Table tool_audit: id UUID, tenant_id VARCHAR, user_id VARCHAR, tool VARCHAR, action VARCHAR, 
    input JSONB, output JSONB, latency_ms INT, status VARCHAR success/error/permission_denied, 
    error_message TEXT, trace_id VARCHAR, correlation_id VARCHAR, timestamp TIMESTAMP default NOW()
    
    :param tenant_id: Tenant identifier
    :param user_id: User identifier
    :param tool: Tool name
    :param action: Action (read/write)
    :param input: Input dict
    :param output: Output dict
    :param latency_ms: Latency in milliseconds
    :param status: Status (success/error/permission_denied)
    :param trace_id: Trace identifier
    :param correlation_id: Correlation identifier
    :param error_message: Optional error message
    :return: str - audit_id
    """
    audit_id = str(uuid.uuid4())
    entry = {
        "id": audit_id,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "tool": tool,
        "action": action,
        "input": json.dumps(input) if input else None,
        "output": json.dumps(output) if output else None,
        "latency_ms": latency_ms,
        "status": status,
        "error_message": error_message,
        "trace_id": trace_id,
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _tool_audit_db.append(entry)
    return audit_id


def get_tool_audit(tenant_id: str = None, tool: str = None, user_id: str = None, status: str = None, limit: int = 100) -> list:
    """Get audit logs with optional filtering."""
    result = _tool_audit_db
    if tenant_id:
        result = [r for r in result if r["tenant_id"] == tenant_id]
    if tool:
        result = [r for r in result if r["tool"] == tool]
    if user_id:
        result = [r for r in result if r["user_id"] == user_id]
    if status:
        result = [r for r in result if r["status"] == status]
    result.sort(key=lambda x: x["timestamp"], reverse=True)
    return result[:limit]


def get_tool_audit_by_id(audit_id: str) -> dict:
    """Get a single audit log by ID."""
    for entry in _tool_audit_db:
        if entry["id"] == audit_id:
            return entry
    return None