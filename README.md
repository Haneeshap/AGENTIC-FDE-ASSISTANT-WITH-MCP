# Day 20-22: Agentic FDE Assistant

## Overview
This project builds upon the Enterprise RAG 15 dashboards to create an Agentic FDE Assistant with MCP (Model Context Protocol) integration. The assistant provides 5 integrated tools (Jira, GitHub, SQL, Slack, Notion) with permission-based access, metrics tracking, and audit logging.

## MCP Server

### Start the Server
```bash
docker-compose up mcp
```

### Available Endpoints

#### Call a Single Tool
```bash
# Grant permission first
curl -X POST "http://localhost:8001/permissions" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "acme", "user_id": "test-user", "tool": "jira", "action": "read", "granted_by": "admin"}'

# Call jira tool
curl -X POST "http://localhost:8001/mcp/call" \
  -H "Content-Type: application/json" \
  -d '{"tool": "jira", "input": {"query": "bug", "tenant_id": "acme"}, "tenant_id": "acme", "user_id": "test-user"}'

# Call sql tool
curl -X POST "http://localhost:8001/mcp/call" \
  -H "Content-Type: application/json" \
  -d '{"tool": "sql", "input": {"query": "SELECT * FROM users", "tenant_id": "acme"}, "tenant_id": "acme", "user_id": "test-user"}'

# Call slack tool
curl -X POST "http://localhost:8001/mcp/call" \
  -H "Content-Type: application/json" \
  -d '{"tool": "slack", "input": {"channel": "#general", "message": "Hello", "tenant_id": "acme"}, "tenant_id": "acme", "user_id": "test-user"}'
```

#### List Available Tools
```bash
curl -X GET "http://localhost:8001/mcp/tools"
```

#### Batch Call Multiple Tools
```bash
curl -X POST "http://localhost:8001/mcp/call/batch" \
  -H "Content-Type: application/json" \
  -d '{"calls": [{"tool": "jira", "input": {"query": "bug", "tenant_id": "acme"}}, {"tool": "github", "input": {"query": "auth", "tenant_id": "acme"}}, {"tool": "sql", "input": {"query": "SELECT 1", "tenant_id": "acme"}}, {"tool": "slack", "input": {"channel": "#general", "message": "Hi", "tenant_id": "acme"}}, {"tool": "notion", "input": {"query": "doc", "tenant_id": "acme"}}], "tenant_id": "acme"}'
```

#### Revoke Permission
```bash
curl -X DELETE "http://localhost:8001/permissions?tenant_id=acme&user_id=test-user&tool=jira&action=read"
```

#### Audit Log Endpoints
```bash
# Get all audit logs for a tenant
curl -X GET "http://localhost:8001/audit/tools?tenant_id=acme&limit=100"

# Get single audit log by ID
curl -X GET "http://localhost:8001/audit/tools/{audit_id}"
```

#### Grant Permission with Expiration
```bash
curl -X POST "http://localhost:8001/permissions" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "acme", "user_id": "test-user", "tool": "slack", "action": "write", "expires_at": "2024-12-31T23:59:59Z", "granted_by": "admin"}'
```

## Individual Tool Examples

### Jira Tool
```bash
# Search for bugs in Jira
curl -X POST "http://localhost:8001/mcp/call" \
  -H "Content-Type: application/json" \
  -d '{"tool": "jira", "input": {"query": "payment", "tenant_id": "acme"}, "tenant_id": "acme", "user_id": "test-user"}'
```

### GitHub Tool
```bash
# Search for configuration files in GitHub
curl -X POST "http://localhost:8001/mcp/call" \
  -H "Content-Type: application/json" \
  -d '{"tool": "github", "input": {"query": "docker-compose", "tenant_id": "acme"}, "tenant_id": "acme", "user_id": "test-user"}'
```

### SQL Tool
```bash
# Execute a SELECT query
curl -X POST "http://localhost:8001/mcp/call" \
  -H "Content-Type: application/json" \
  -d '{"tool": "sql", "input": {"query": "SELECT id, name FROM products WHERE price > 100", "tenant_id": "acme"}, "tenant_id": "acme", "user_id": "test-user"}'

# Note: DELETE, INSERT, UPDATE statements are blocked
curl -X POST "http://localhost:8001/mcp/call" \
  -H "Content-Type: application/json" \
  -d '{"tool": "sql", "input": {"query": "DELETE FROM users", "tenant_id": "acme"}, "tenant_id": "acme", "user_id": "test-user"}' \
  # Returns 403: Only SELECT allowed
```

### Slack Tool
```bash
# Send a message to a Slack channel
curl -X POST "http://localhost:8001/mcp/call" \
  -H "Content-Type: application/json" \
  -d '{"tool": "slack", "input": {"channel": "#general", "message": "Daily report available", "tenant_id": "acme"}, "tenant_id": "acme", "user_id": "test-user"}'
```

### Notion Tool
```bash
# Search for pages in Notion
curl -X POST "http://localhost:8001/mcp/call" \
  -H "Content-Type: application/json" \
  -d '{"tool": "notion", "input": {"query": "architecture", "tenant_id": "acme"}, "tenant_id": "acme", "user_id": "test-user"}'
```

## Prometheus Metrics

The following metrics are available at `http://localhost:8001/metrics`:

- `tool_calls_total`: Counter - Total tool calls by tool, tenant_id, status
- `tool_latency_seconds`: Histogram - Tool latency by tool (buckets: 0.01, 0.05, 0.1, 0.5, 1, 2, 5)
- `tool_error_total`: Counter - Total tool errors by tool, error_type
- `tool_cost_per_call`: Gauge - Cost per tool call by tool
- `permission_denied_total`: Counter - Total permission denied calls by tool, tenant_id
- `tool_audit_total`: Counter - Total tool audit entries by tool, status

## Development

### Running Tests
```bash
pytest tests/test_p2_day20_22.py -v
```

### Running with Docker
```bash
docker-compose build
docker-compose up mcp
```

### Manual Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.mcp.server:app --host 0.0.0.0 --port 8001
```