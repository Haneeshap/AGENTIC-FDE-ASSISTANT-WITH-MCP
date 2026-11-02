def slack_tool(input: dict) -> dict:
    """
    Slack tool for sending messages.
    
    Input: {channel: str, message: str, tenant_id: str}
    Output: {ts: str timestamp like "1620000000.123456", channel: str, message: str, status: str sent}
    
    Permission: slack:write (more sensitive than read)
    """
    import os
    channel = input.get("channel", "")
    message = input.get("message", "")
    tenant_id = input.get("tenant_id", "")
    
    # Check if real Slack bot token exists
    if os.environ.get("SLACK_BOT_TOKEN"):
        # Real implementation would call Slack client
        # For now, return mock
        ts = "1620000000.123456"
        return {
            "ts": ts,
            "channel": channel,
            "message": message,
            "status": "sent",
        }
    
    # Mock: return ts mock
    ts = "1620000000.123456"
    return {
        "ts": ts,
        "channel": channel,
        "message": message,
        "status": "sent",
    }