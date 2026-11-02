import time
import asyncio
from typing import Dict, Any, Optional

from fastapi import FastAPI

# Import tools
import sys
sys.path.insert(0, '/app')
from app.mcp.tools.jira import jira_tool
from app.mcp.tools.github import github_tool
from app.mcp.tools.sql import sql_tool
from app.mcp.tools.slack import slack_tool
from app.mcp.tools.notion import notion_tool

from app.auth.permissions import check_permission
from app.audit.tool_audit import log_tool_call
from app.metrics.tool_metrics import (
    record_tool_call,
    permission_denied_total,
    tool_error_total,
    tool_calls_total,
    tool_latency_seconds,
)


class MCPServer:
    def __init__(self):
        self.tools: Dict[str, Any] = {
            'jira': jira_tool,
            'github': github_tool,
            'sql': sql_tool,
            'slack': slack_tool,
            'notion': notion_tool,
        }
        self.app = FastAPI(title='MCP Server')
        from app.routes.mcp import router
        self.app.include_router(router)

    async def call_tool(
        self,
        tool_name: str,
        input: dict,
        tenant_id: str,
        user_id: str,
        trace_id: str,
        correlation_id: str,
    ) -> dict:
        action = 'read' if tool_name != 'slack' else 'write'
        permitted = check_permission(tenant_id, user_id, tool_name, action=action)

        if not permitted:
            permission_denied_total.labels(tool=tool_name, tenant_id=tenant_id).inc()
            log_tool_call(
                tenant_id=tenant_id,
                user_id=user_id,
                tool=tool_name,
                action=action,
                input=input,
                output={},
                latency_ms=0,
                status='permission_denied',
                trace_id=trace_id,
                correlation_id=correlation_id,
                error_message='Permission denied',
            )
            return {
                'output': None,
                'latency_ms': 0,
                'trace_id': trace_id,
                'cost': 0.0,
                'permission_granted': False,
                'error': '403 Permission denied',
            }

        start_time = time.time()
        try:
            tool_func = self.tools[tool_name]
            result = tool_func(input)
        except Exception as e:
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            tool_error_total.labels(tool=tool_name, error_type=type(e).__name__).inc()
            log_tool_call(
                tenant_id=tenant_id,
                user_id=user_id,
                tool=tool_name,
                action=action,
                input=input,
                output={},
                latency_ms=latency_ms,
                status='error',
                trace_id=trace_id,
                correlation_id=correlation_id,
                error_message=str(e),
            )
            return {
                'output': None,
                'latency_ms': latency_ms,
                'trace_id': trace_id,
                'cost': 0.0,
                'permission_granted': True,
                'error': str(e),
            }

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        tool_calls_total.labels(tool=tool_name, tenant_id=tenant_id, status='success').inc()
        tool_latency_seconds.labels(tool=tool_name).observe((end_time - start_time))
        log_tool_call(
            tenant_id=tenant_id,
            user_id=user_id,
            tool=tool_name,
            action=action,
            input=input,
            output=result if isinstance(result, dict) else {'output': result},
            latency_ms=latency_ms,
            status='success',
            trace_id=trace_id,
            correlation_id=correlation_id,
        )
        cost_map = {
            'jira': 0.001,
            'github': 0.001,
            'sql': 0.0005,
            'slack': 0.002,
            'notion': 0.001,
        }
        cost = cost_map.get(tool_name, 0.0)
        return {
            'output': result if isinstance(result, dict) else {'issues': result},
            'latency_ms': latency_ms,
            'trace_id': trace_id,
            'cost': cost,
            'permission_granted': True,
        }


mcp_server = MCPServer()
app = mcp_server.app
