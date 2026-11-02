-- Migration: 003_permissions_audit.sql
-- Creates the permissions table and tool_audit table

-- Create permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY,
    tenant_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    tool VARCHAR NOT NULL,
    action VARCHAR NOT NULL CHECK (action IN ('read', 'write')),
    granted_by VARCHAR NOT NULL,
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Create index on permissions for fast lookup
CREATE INDEX IF NOT EXISTS idx_permissions_tenant_user_tool
    ON permissions (tenant_id, user_id, tool);

-- Create tool_audit table
CREATE TABLE IF NOT EXISTS tool_audit (
    id UUID PRIMARY KEY,
    tenant_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    tool VARCHAR NOT NULL,
    action VARCHAR NOT NULL,
    input JSONB,
    output JSONB,
    latency_ms INT,
    status VARCHAR NOT NULL CHECK (status IN ('success', 'error', 'permission_denied')),
    error_message TEXT,
    trace_id VARCHAR,
    correlation_id VARCHAR,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create index on tool_audit for fast lookup
CREATE INDEX IF NOT EXISTS idx_tool_audit_tenant_tool
    ON tool_audit (tenant_id, tool);

CREATE INDEX IF NOT EXISTS idx_tool_audit_timestamp
    ON tool_audit (timestamp DESC);