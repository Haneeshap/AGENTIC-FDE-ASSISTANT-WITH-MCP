from prometheus_client import Counter, Histogram, Gauge

# Tool calls total counter - labels: tool, tenant_id, status
tool_calls_total = Counter(
    "tool_calls_total",
    "Total tool calls",
    ["tool", "tenant_id", "status"],
)

# Tool latency histogram - labels: tool, buckets: 0.01,0.05,0.1,0.5,1,2,5
tool_latency_seconds = Histogram(
    "tool_latency_seconds",
    "Tool latency in seconds",
    ["tool"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5],
)

# Tool error total counter - labels: tool, error_type
tool_error_total = Counter(
    "tool_error_total",
    "Total tool errors",
    ["tool", "error_type"],
)

# Tool cost per call gauge - labels: tool
tool_cost_per_call = Gauge(
    "tool_cost_per_call",
    "Cost per tool call",
    ["tool"],
)

# Permission denied total counter - labels: tool, tenant_id
permission_denied_total = Counter(
    "permission_denied_total",
    "Total permission denied calls",
    ["tool", "tenant_id"],
)

# Tool audit total counter - labels: tool, status
tool_audit_total = Counter(
    "tool_audit_total",
    "Total tool audit entries",
    ["tool", "status"],
)


def record_tool_call(tenant_id: str, user_id: str, tool: str, action: str,
                     latency_ms: int, status: str, error_type: str = None) -> dict:
    """
    Record metrics for a tool call.
    
    :param tenant_id: Tenant identifier
    :param user_id: User identifier
    :param tool: Tool name
    :param action: Action (read/write)
    :param latency_ms: Latency in milliseconds
    :param status: Status (success/error/permission_denied)
    :param error_type: Optional error type
    :return: dict of recorded metrics
    """
    # Increment call counter
    status_label = status if status else "error"
    tool_calls_total.labels(tool=tool, tenant_id=tenant_id, status=status_label).inc()
    
    # Observe latency
    tool_latency_seconds.labels(tool=tool).observe(latency_ms / 1000.0)
    
    # Increment error counter if there's an error
    if error_type:
        tool_error_total.labels(tool=tool, error_type=error_type).inc()
    
    # Update cost gauge
    cost_map = {
        "jira": 0.001,
        "github": 0.001,
        "sql": 0.0005,
        "slack": 0.002,
        "notion": 0.001,
    }
    cost = cost_map.get(tool, 0.0)
    tool_cost_per_call.labels(tool=tool).set(cost)
    
    # Increment audit counter
    tool_audit_total.labels(tool=tool, status=status_label).inc()
    
    return {
        "tool_calls_total": tool_calls_total._value,
        "latency": tool_latency_seconds._value,
        "error_total": tool_error_total._value,
        "cost": tool_cost_per_call._value,
        "audit_total": tool_audit_total._value,
    }