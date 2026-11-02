def github_tool(input: dict) -> dict:
    """
    GitHub tool for searching files.
    
    Input: {query: str, repo: str optional, tenant_id: str, max_results: int=10}
    Output: {files: [{path: str, repo: str, content: str snippet contains query, url: str, score: float 0-1}]}
    """
    import os
    query = input.get("query", "")
    repo = input.get("repo", "")
    tenant_id = input.get("tenant_id", "")
    max_results = input.get("max_results", 10)
    
    # Check if real GitHub token exists
    if os.environ.get("GITHUB_TOKEN"):
        # Real implementation would call GitHub client
        pass
    
    # Mock: generate 5 mock files
    files = []
    extensions = [".py", ".js", ".ts", ".json", ".yaml"]
    
    for i in range(min(max_results, 5)):
        path = f"{query.replace(' ', '_')}{i}.py" if query else f"sample{i}.py"
        content_snippet = f"# {query} related content" if query else f"# Sample content {i}"
        # Check if query is in content for scoring
        score = 0.8 if query in content_snippet else 0.5
        
        file_entry = {
            "path": path,
            "repo": repo or "org/repo",
            "content": content_snippet,
            "url": f"https://github.com/org/repo/blob/main/{path}",
            "score": round(score, 2),
        }
        files.append(file_entry)
    
    return {"files": files}