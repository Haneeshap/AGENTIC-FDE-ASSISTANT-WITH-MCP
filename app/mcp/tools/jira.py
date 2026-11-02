def jira_tool(input: dict) -> dict:
    """
    Jira tool for searching issues.
    
    Input: {query: str, project: str optional, tenant_id: str, max_results: int=10}
    Output: {issues: [{id: str, key: str like "PROJ-123", title: str contains query keyword, status: str open/in_progress/done, assignee: str, url: str, priority: str high/medium/low}]}
    """
    import os
    query = input.get("query", "")
    project = input.get("project", "")
    tenant_id = input.get("tenant_id", "")
    max_results = input.get("max_results", 10)
    
    # Check if real JIRA API key exists
    if os.environ.get("JIRA_API_KEY"):
        # Real implementation would call JIRA client
        # For now, return mock
        pass
    
    # Mock: generate 5 mock issues with query keyword in title
    issues = []
    statuses = ["open", "in_progress", "done"]
    priorities = ["high", "medium", "low"]
    
    for i in range(min(max_results, 5)):
        issue_key = f"PROJ-{123 + i}"
        title = f"Bug in {query} flow {issue_key}" if query else f"Sample issue {issue_key}"
        issue = {
            "id": str(1000 + i),
            "key": issue_key,
            "title": title,
            "status": statuses[i % 3],
            "assignee": f"user{i}",
            "url": f"https://jira.example.com/browse/{issue_key}",
            "priority": priorities[i % 3],
        }
        issues.append(issue)
    
    return {"issues": issues}