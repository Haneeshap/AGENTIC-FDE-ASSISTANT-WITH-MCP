def notion_tool(input: dict) -> dict:
    """
    Notion tool for searching pages.
    
    Input: {query: str, tenant_id: str, max_results: int=10}
    Output: {pages: [{id: str, title: str contains query, url: str <https://notion.so/page-id>, content_snippet: str, score: float}]}
    
    Permission: notion:read
    """
    import os
    query = input.get("query", "")
    tenant_id = input.get("tenant_id", "")
    max_results = input.get("max_results", 10)
    
    # Check if real Notion API key exists
    if os.environ.get("NOTION_API_KEY"):
        # Real implementation would call Notion client
        pass
    
    # Mock: generate 5 mock pages
    pages = []
    
    for i in range(min(max_results, 5)):
        page_title = f"{query} documentation page" if query else f"Sample documentation page {i}"
        pages.append({
            "id": f"page-{i}",
            "title": page_title,
            "url": f"https://notion.so/page-id-{i}",
            "content_snippet": f"This page contains information about {query}" if query else f"Sample content {i}",
            "score": round(0.9 - i * 0.15, 2),
        })
    
    return {"pages": pages}