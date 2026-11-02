import os
import re
import time
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError

# Global engine (would be configured from env in production)
_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        db_url = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/mcp")
        _engine = create_engine(db_url)
    return _engine

def sql_tool(input: dict) -> dict:
    """
    SQL tool for executing read-only queries.

    Input: {query: str, tenant_id: str, max_rows: int=100}
    Output: {rows: [dict], columns: [str], row_count: int, execution_time_ms: int}

    Security: ONLY SELECT allowed. Check: upper query contains DELETE|DROP|UPDATE|INSERT|ALTER|TRUNCATE|CREATE -> raise 403 "Only SELECT allowed". Also block multiple statements ";" unless SELECT.
    Execute: on Postgres, with RLS WHERE tenant_id=:tenant_id if not present in query, add filter. Use SQLAlchemy text query.
    Permission: sql:read
    Cost: $0.0005
    Audit: log full query + row_count
    """
    import os
    query = input.get("query", "")
    tenant_id = input.get("tenant_id", "")
    max_rows = input.get("max_rows", 100)

    # Security: Check for blocked keywords
    upper_query = query.upper().strip()

    # Block dangerous statements
    dangerous_keywords = ["DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE"]
    for kw in dangerous_keywords:
        if kw in upper_query:
            raise ValueError(f"Only SELECT allowed. Blocked keyword: {kw}")

    # Block multiple statements unless it's SELECT
    # Check if there's a semicolon not inside a SELECT
    stripped = query.strip()
    if ";" in stripped:
        # Check if the first statement is SELECT
        first_stmt = stripped.split(";")[0].strip()
        if not first_stmt.upper().startswith("SELECT"):
            raise ValueError("Multiple statements not allowed. Only SELECT is permitted.")

    # Execute query with RLS (Row Level Security) - add tenant_id filter if not present
    engine = _get_engine()

    # Add tenant_id filter if not already in the query
    if f"tenant_id:{tenant_id}" not in query.lower() and f"tenant_id = '{tenant_id}'" not in query and f"tenant_id = '{tenant_id}'" not in query and f"SET tenant_id='{tenant_id}'" not in query.upper():
        # Try to add WHERE clause if there's no WHERE yet
        if "where" not in upper_query:
            query = f"{query} WHERE tenant_id = '{tenant_id}'"
        else:
            query = f"{query} AND tenant_id = '{tenant_id}'"

    start_time = time.time()

    try:
        with _engine.connect() as conn:
            # Execute with SQLAlchemy text
            sel = text(query)
            result = conn.execute(sel)
            rows = [dict(zip(result.keys(), row)) for row in result.fetchall()][:max_rows]
            columns = list(result.keys())
            execution_time_ms = int((time.time() - start_time) * 1000)
    except Exception as e:
        raise ValueError(f"Query execution error: {str(e)}")

    return {
        "rows": rows,
        "columns": columns,
        "row_count": len(rows),
        "execution_time_ms": execution_time_ms,
    }