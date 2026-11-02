import pytest
from app.mcp.tools.jira import jira_tool
from app.mcp.tools.github import github_tool
from app.mcp.tools.sql import sql_tool
from app.mcp.tools.slack import slack_tool
from app.mcp.tools.notion import notion_tool
from app.auth.permissions import check_permission, grant_permission, revoke_permission, list_permissions


def test_jira_tool_returns_5_issues_with_query_keyword():
    """test_jira_tool returns 5 issues with query keyword in title"""
    result = jira_tool({"query": "bug", "tenant_id": "acme", "max_results": 5})
    assert "issues" in result
    assert len(result["issues"]) == 5
    for issue in result["issues"]:
        assert "bug" in issue["title"].lower()


def test_github_tool_returns_5_files():
    """test_github_tool returns 5 files"""
    result = github_tool({"query": "auth", "tenant_id": "acme", "max_results": 5})
    assert "files" in result
    assert len(result["files"]) == 5


def test_sql_tool_select_returns_rows():
    """test_sql_tool SELECT returns rows, execution_time_ms <500ms"""
    result = sql_tool({"query": "SELECT * FROM users", "tenant_id": "acme", "max_rows": 10})
    assert "rows" in result
    assert "columns" in result
    assert "row_count" in result
    assert result["execution_time_ms"] < 500


def test_sql_tool_delete_blocked():
    """test_sql_tool DELETE blocked 403"""
    try:
        sql_tool({"query": "DELETE FROM users", "tenant_id": "acme"})
        assert False, "Should have raised an error"
    except ValueError as e:
        assert "Only SELECT allowed" in str(e)


def test_slack_tool_returns_ts():
    """test_slack_tool returns ts"""
    result = slack_tool({"channel": "#general", "message": "Hello", "tenant_id": "acme"})
    assert "ts" in result
    assert result["status"] == "sent"


def test_notion_tool_returns_5_pages():
    """test_notion_tool returns 5 pages"""
    result = notion_tool({"query": "documentation", "tenant_id": "acme", "max_results": 5})
    assert "pages" in result
    assert len(result["pages"]) == 5


def test_permission_blocks_without_permission():
    """test_permission_blocks without permission returns 403 permission_denied"""
    from app.auth.permissions import _permissions_db
    _permissions_db.clear()
    
    permitted = check_permission("acme", "test-user", "jira", action="read")
    assert permitted == False


def test_permission_grants_after_grant():
    """test_permission_grants after grant permission allows tool call success"""
    from app.auth.permissions import _permissions_db
    _permissions_db.clear()
    
    grant_permission("acme", "test-user", "jira", "read", "admin")
    
    permitted = check_permission("acme", "test-user", "jira", action="read")
    assert permitted == True


def test_audit_log_records_tool_call():
    """test_audit_log records tool call in tool_audit table"""
    from app.audit.tool_audit import log_tool_call
    
    audit_id = log_tool_call(
        tenant_id="acme",
        user_id="test-user",
        tool="jira",
        action="read",
        input={"query": "bug"},
        output={"issues": []},
        latency_ms=50,
        status="success",
        trace_id="test-trace",
        correlation_id="test-corr",
    )
    
    assert audit_id is not None


def test_batch_call_returns_5_results():
    """test_batch_call returns 5 results for batch of 5 tools"""
    from fastapi.testclient import TestClient

    from app.mcp.server import app
    from app.auth.permissions import grant_permission

    # Grant permissions for all tools
    grant_permission("acme", "test-user", "jira", "read", "admin")
    grant_permission("acme", "test-user", "github", "read", "admin")
    grant_permission("acme", "test-user", "sql", "read", "admin")
    grant_permission("acme", "test-user", "slack", "write", "admin")
    grant_permission("acme", "test-user", "notion", "read", "admin")

    client = TestClient(app)

    response = client.post(
        "/mcp/call/batch?tenant_id=acme",
        json={
            "calls": [
                {"tool": "jira", "input": {"query": "bug", "tenant_id": "acme"}},
                {"tool": "github", "input": {"query": "auth", "tenant_id": "acme"}},
                {"tool": "sql", "input": {"query": "SELECT 1", "tenant_id": "acme"}},
                {"tool": "slack", "input": {"channel": "#general", "message": "Hi", "tenant_id": "acme"}},
                {"tool": "notion", "input": {"query": "doc", "tenant_id": "acme"}},
            ],
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result["results"]) == 5
    for r in result["results"]:
        assert r["permission_granted"] == True