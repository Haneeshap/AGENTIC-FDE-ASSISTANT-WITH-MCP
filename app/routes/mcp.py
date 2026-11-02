from fastapi import APIRouter
from typing import Optional, Dict, Any, List
import time
import uuid

from app.mcp.server import MCPServer
from app.auth.permissions import check_permission, grant_permission, revoke_permission, list_permissions
from app.audit.tool_audit import log_tool_call, get_tool_audit, get_tool_audit_by_id
from app.metrics.tool_metrics import record_tool_call, permission_denied_total

router = APIRouter()

mcp_server = MCPServer()


@router.post('/mcp/call')
async def call_tool_endpoint(
    tool: str,
    input: dict,
    tenant_id: str = 'test-user',
    user_id: str = 'test-user',
    trace_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
):
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    start_time = time.time()

    action = 'read' if tool != 'slack' else 'write'
    permitted = check_permission(tenant_id, user_id, tool, action=action)

    latency_ms = int((time.time() - start_time) * 1000)

    if not permitted:
        permission_denied_total.labels(tool=tool, tenant_id=tenant_id).inc()

        from app.audit.tool_audit import log_tool_call
        log_tool_call(
            tenant_id=tenant_id,
            user_id=user_id,
            tool=tool,
            action=action,
            input=input,
            output={},
            latency_ms=latency_ms,
            status='permission_denied',
            trace_id=trace_id,
            correlation_id=correlation_id,
            error_message='Permission denied',
        )

        raise HTTPException(status_code=403, detail='Permission denied')

    try:
        result = await mcp_server.call_tool(
            tool_name=tool,
            input=input,
            tenant_id=tenant_id,
            user_id=user_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
        )
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error_type = type(e).__name__

        record_tool_call(
            tenant_id=tenant_id,
            user_id=user_id,
            tool=tool,
            action=action,
            latency_ms=latency_ms,
            status='error',
            error_type=error_type,
        )

        from app.audit.tool_audit import log_tool_call
        log_tool_call(
            tenant_id=tenant_id,
            user_id=user_id,
            tool=tool,
            action=action,
            input=input,
            output={},
            latency_ms=latency_ms,
            status='error',
            trace_id=trace_id,
            correlation_id=correlation_id,
            error_message=str(e),
        )

        raise HTTPException(status_code=500, detail=str(e))

    latency_ms = int((time.time() - start_time) * 1000)

    record_tool_call(
        tenant_id=tenant_id,
        user_id=user_id,
        tool=tool,
        action=action,
        latency_ms=latency_ms,
        status='success',
    )

    log_tool_call(
        tenant_id=tenant_id,
        user_id=user_id,
        tool=tool,
        action=action,
        input=input,
        output=result.get('output', result),
        latency_ms=latency_ms,
        status='success',
        trace_id=trace_id,
        correlation_id=correlation_id,
    )

    return {
        'output': result.get('output'),
        'latency_ms': latency_ms,
        'trace_id': trace_id,
        'cost': result.get('cost', 0.0),
        'permission_granted': result.get('permission_granted', True),
    }


@router.get('/mcp/tools')
async def list_mcp_tools():
    tools_info = [
        {
            'name': 'jira',
            'description': 'Search Jira issues',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'},
                    'project': {'type': 'string'},
                    'tenant_id': {'type': 'string'},
                    'max_results': {'type': 'integer', 'default': 10},
                },
                'required': ['query', 'tenant_id'],
            },
            'output_schema': {
                'type': 'object',
                'properties': {
                    'issues': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string'},
                                'key': {'type': 'string'},
                                'title': {'type': 'string'},
                                'status': {'type': 'string'},
                                'assignee': {'type': 'string'},
                                'url': {'type': 'string'},
                                'priority': {'type': 'string'},
                            },
                        },
                    }
                },
            },
            'permission_required': 'jira:read',
            'cost_per_call': 0.001,
        },
        {
            'name': 'github',
            'description': 'Search GitHub files',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'},
                    'repo': {'type': 'string'},
                    'tenant_id': {'type': 'string'},
                    'max_results': {'type': 'integer', 'default': 10},
                },
                'required': ['query', 'tenant_id'],
            },
            'output_schema': {
                'type': 'object',
                'properties': {
                    'files': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'path': {'type': 'string'},
                                'repo': {'type': 'string'},
                                'content': {'type': 'string'},
                                'url': {'type': 'string'},
                                'score': {'type': 'float'},
                            },
                        },
                    }
                },
            },
            'permission_required': 'github:read',
            'cost_per_call': 0.001,
        },
        {
            'name': 'sql',
            'description': 'Execute SQL SELECT query',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'},
                    'tenant_id': {'type': 'string'},
                    'max_rows': {'type': 'integer', 'default': 100},
                },
                'required': ['query', 'tenant_id'],
            },
            'output_schema': {
                'type': 'object',
                'properties': {
                    'rows': {'type': 'array'},
                    'columns': {'type': 'array'},
                    'row_count': {'type': 'integer'},
                    'execution_time_ms': {'type': 'integer'},
                },
            },
            'permission_required': 'sql:read',
            'cost_per_call': 0.0005,
        },
        {
            'name': 'slack',
            'description': 'Send message to Slack channel',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'channel': {'type': 'string'},
                    'message': {'type': 'string'},
                    'tenant_id': {'type': 'string'},
                },
                'required': ['channel', 'message', 'tenant_id'],
            },
            'output_schema': {
                'type': 'object',
                'properties': {
                    'ts': {'type': 'string'},
                    'channel': {'type': 'string'},
                    'message': {'type': 'string'},
                    'status': {'type': 'string'},
                },
            },
            'permission_required': 'slack:write',
            'cost_per_call': 0.002,
        },
        {
            'name': 'notion',
            'description': 'Search Notion pages',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'},
                    'tenant_id': {'type': 'string'},
                    'max_results': {'type': 'integer', 'default': 10},
                },
                'required': ['query', 'tenant_id'],
            },
            'output_schema': {
                'type': 'object',
                'properties': {
                    'pages': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string'},
                                'title': {'type': 'string'},
                                'url': {'type': 'string'},
                                'content_snippet': {'type': 'string'},
                                'score': {'type': 'float'},
                            },
                        },
                    }
                },
            },
            'permission_required': 'notion:read',
            'cost_per_call': 0.001,
        },
    ]
    return {'tools': tools_info}


@router.post('/mcp/call/batch')
async def batch_call(
    body: dict,
    tenant_id: str = None,
):
    results = []
    calls = body.get('calls', [])
    user_id = body.get('user_id', 'test-user')
    if tenant_id is None:
        tenant_id = body.get('tenant_id', '')

    for call in calls:
        tool = call.get('tool', '')
        input_data = call.get('input', {})

        start_time = time.time()

        action = 'read' if tool != 'slack' else 'write'
        permitted = check_permission(tenant_id, user_id, tool, action=action)

        if not permitted:
            permission_denied_total.labels(tool=tool, tenant_id=tenant_id).inc()

            from app.audit.tool_audit import log_tool_call
            log_tool_call(
                tenant_id=tenant_id,
                user_id=user_id,
                tool=tool,
                action=action,
                input=input_data,
                output={},
                latency_ms=0,
                status='permission_denied',
                trace_id='',
                correlation_id='',
                error_message='Permission denied',
            )

            results.append({
                'tool': tool,
                'output': None,
                'latency_ms': 0,
                'permission_granted': False,
            })
            continue

        try:
            result = await mcp_server.call_tool(
                tool_name=tool,
                input=input_data,
                tenant_id=tenant_id,
                user_id=user_id,
                trace_id='',
                correlation_id='',
            )
            latency_ms = int((time.time() - start_time) * 1000)

            results.append({
                'tool': tool,
                'output': result.get('output'),
                'latency_ms': latency_ms,
                'permission_granted': result.get('permission_granted', True),
            })
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            results.append({
                'tool': tool,
                'output': None,
                'latency_ms': latency_ms,
                'permission_granted': False,
            })

    return {'results': results}


@router.post('/permissions')
async def grant_permission_endpoint(
    tenant_id: str,
    user_id: str,
    tool: str,
    action: str,
    expires_at: Optional[str] = None,
    granted_by: str = 'admin',
):
    granted_by = 'admin'

    grant_permission(tenant_id, user_id, tool, action, granted_by, expires_at)

    return {
        'granted': True,
        'tenant_id': tenant_id,
        'user_id': user_id,
        'tool': tool,
        'action': action,
        'granted_by': granted_by,
    }


@router.delete('/permissions')
async def revoke_permission_endpoint(
    tenant_id: str,
    user_id: str,
    tool: str,
    action: str,
):
    count = revoke_permission(tenant_id, user_id, tool, action)

    return {'revoked': count > 0}


@router.get('/permissions')
async def list_permissions_endpoint(
    tenant_id: str,
    user_id: str,
):
    perms = list_permissions(tenant_id, user_id)
    return {'permissions': perms}


@router.get('/audit/tools')
async def get_audit_tools(
    tenant_id: str = None,
    tool: str = None,
    user_id: str = None,
    status: str = None,
    limit: int = 100,
):
    logs = get_tool_audit(tenant_id=tenant_id, tool=tool, user_id=user_id, status=status, limit=limit)
    return {'logs': logs}


@router.get('/audit/tools/{audit_id}')
async def get_audit_tool_by_id(audit_id: str):
    from fastapi import HTTPException
    log = get_tool_audit_by_id(audit_id)
    if not log:
        raise HTTPException(status_code=404, detail='Audit log not found')
    return {'log': log}
