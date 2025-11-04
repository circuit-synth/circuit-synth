-- TAC-X Database Schema - Initial Migration
-- Version: 1.0.0
-- Date: 2025-11-03
-- Description: Hybrid architecture with 4-stage pipeline + dynamic helper agents

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Core Task Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS tac_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_number VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    -- Status: running, completed, errored, blocked, cancelled
    current_stage VARCHAR(50),
    -- Current stage: planning, building, reviewing, pr_creation
    workflow_config JSONB,
    -- The YAML workflow configuration used
    worktree_path TEXT,
    branch_name VARCHAR(255),
    total_cost DECIMAL(10, 6) DEFAULT 0,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    -- Additional fields: GitHub issue data, coordinator info, etc.

    CONSTRAINT valid_status CHECK (status IN ('running', 'completed', 'errored', 'blocked', 'cancelled')),
    CONSTRAINT valid_stage CHECK (current_stage IS NULL OR current_stage IN ('planning', 'building', 'reviewing', 'pr_creation'))
);

CREATE INDEX idx_tasks_issue_number ON tac_tasks(issue_number);
CREATE INDEX idx_tasks_status ON tac_tasks(status);
CREATE INDEX idx_tasks_created_at ON tac_tasks(created_at DESC);

-- ============================================================================
-- Stage Execution Tracking (Main 4 Stages)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tac_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tac_tasks(id) ON DELETE CASCADE,
    stage_name VARCHAR(50) NOT NULL,
    -- planning, building, reviewing, pr_creation
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- Status: pending, running, completed, errored, skipped
    provider VARCHAR(100),
    -- openrouter, anthropic, openai, etc.
    model VARCHAR(100),
    -- google/gemini-2.5-flash, claude-sonnet-4-5, etc.
    temperature DECIMAL(3, 2),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost DECIMAL(10, 6) DEFAULT 0,
    output_file TEXT,
    -- Path to plan.md, review.md, pr_url, etc.
    error_message TEXT,
    metadata JSONB,
    -- Prompt used, fallback attempts, retry count, etc.

    CONSTRAINT valid_stage_status CHECK (status IN ('pending', 'running', 'completed', 'errored', 'skipped')),
    CONSTRAINT valid_stage_name CHECK (stage_name IN ('planning', 'building', 'reviewing', 'pr_creation'))
);

CREATE INDEX idx_stages_task_id ON tac_stages(task_id);
CREATE INDEX idx_stages_status ON tac_stages(status);
CREATE INDEX idx_stages_started_at ON tac_stages(started_at DESC);

-- ============================================================================
-- Helper Agent Tracking (Dynamically Spawned)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tac_helper_agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tac_tasks(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES tac_stages(id) ON DELETE CASCADE,
    -- Which stage spawned this helper
    agent_name VARCHAR(255) NOT NULL,
    -- research-agent-abc123, test-agent-def456, etc.
    agent_template VARCHAR(100) NOT NULL,
    -- research-agent, test-agent, security-scanner, etc.
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    -- Status: running, completed, errored, interrupted
    provider VARCHAR(100),
    model VARCHAR(100),
    session_id VARCHAR(255),
    -- Claude SDK session ID for resumption
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost DECIMAL(10, 6) DEFAULT 0,
    result_summary TEXT,
    -- AI-generated 2-sentence summary of what agent did
    result_data JSONB,
    -- Structured output from agent (findings, files created, etc.)
    metadata JSONB,

    CONSTRAINT valid_helper_status CHECK (status IN ('running', 'completed', 'errored', 'interrupted'))
);

CREATE INDEX idx_helpers_task_id ON tac_helper_agents(task_id);
CREATE INDEX idx_helpers_stage_id ON tac_helper_agents(stage_id);
CREATE INDEX idx_helpers_template ON tac_helper_agents(agent_template);
CREATE INDEX idx_helpers_status ON tac_helper_agents(status);

-- ============================================================================
-- Event Logging (EVERYTHING goes here)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tac_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tac_tasks(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES tac_stages(id) ON DELETE CASCADE,
    helper_agent_id UUID REFERENCES tac_helper_agents(id) ON DELETE CASCADE,
    event_category VARCHAR(50) NOT NULL,
    -- stage, helper, hook, system, coordinator
    event_type VARCHAR(100) NOT NULL,
    -- PreToolUse, PostToolUse, TextBlock, ThinkingBlock, Error, Info, Warning, etc.
    content TEXT,
    -- Human-readable event description
    summary TEXT,
    -- AI-generated 15-word summary (like multi-agent-orchestration does)
    payload JSONB,
    -- Full event data (tool args, file diffs, response, etc.)
    timestamp TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_event_category CHECK (event_category IN ('stage', 'helper', 'hook', 'system', 'coordinator'))
);

CREATE INDEX idx_events_task_id_timestamp ON tac_events(task_id, timestamp DESC);
CREATE INDEX idx_events_stage_id_timestamp ON tac_events(stage_id, timestamp DESC);
CREATE INDEX idx_events_helper_id_timestamp ON tac_events(helper_agent_id, timestamp DESC);
CREATE INDEX idx_events_category ON tac_events(event_category);
CREATE INDEX idx_events_type ON tac_events(event_type);

-- ============================================================================
-- Agent Template Registry
-- ============================================================================

CREATE TABLE IF NOT EXISTS tac_agent_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    -- research-agent, test-agent, security-scanner, etc.
    description TEXT,
    system_prompt TEXT NOT NULL,
    tools TEXT[],
    -- Array of tool names: ['Read', 'Grep', 'Bash']
    model VARCHAR(100) DEFAULT 'sonnet',
    temperature DECIMAL(3, 2) DEFAULT 1.0,
    color VARCHAR(50),
    -- For UI display: blue, green, red, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    -- Additional YAML frontmatter fields
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_templates_name ON tac_agent_templates(name);
CREATE INDEX idx_templates_active ON tac_agent_templates(is_active);

-- ============================================================================
-- Cost Tracking Rollup (For Fast Queries)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tac_cost_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tac_tasks(id) ON DELETE CASCADE,
    date DATE DEFAULT CURRENT_DATE,
    total_cost DECIMAL(10, 6) DEFAULT 0,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    stage_costs JSONB,
    -- { "planning": 0.05, "building": 0.12, ... }
    helper_costs JSONB,
    -- { "research-agent": 0.03, "test-agent": 0.02, ... }
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_task_date UNIQUE (task_id, date)
);

CREATE INDEX idx_cost_summary_task_id ON tac_cost_summary(task_id);
CREATE INDEX idx_cost_summary_date ON tac_cost_summary(date DESC);

-- ============================================================================
-- Triggers for Auto-Update Timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tac_agent_templates_updated_at
    BEFORE UPDATE ON tac_agent_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tac_cost_summary_updated_at
    BEFORE UPDATE ON tac_cost_summary
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to update task total costs automatically
CREATE OR REPLACE FUNCTION update_task_costs()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE tac_tasks
    SET
        total_cost = (
            SELECT COALESCE(SUM(cost), 0)
            FROM tac_stages
            WHERE task_id = NEW.task_id
        ) + (
            SELECT COALESCE(SUM(cost), 0)
            FROM tac_helper_agents
            WHERE task_id = NEW.task_id
        ),
        total_input_tokens = (
            SELECT COALESCE(SUM(input_tokens), 0)
            FROM tac_stages
            WHERE task_id = NEW.task_id
        ) + (
            SELECT COALESCE(SUM(input_tokens), 0)
            FROM tac_helper_agents
            WHERE task_id = NEW.task_id
        ),
        total_output_tokens = (
            SELECT COALESCE(SUM(output_tokens), 0)
            FROM tac_stages
            WHERE task_id = NEW.task_id
        ) + (
            SELECT COALESCE(SUM(output_tokens), 0)
            FROM tac_helper_agents
            WHERE task_id = NEW.task_id
        )
    WHERE id = NEW.task_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_task_costs_on_stage_change
    AFTER INSERT OR UPDATE OF cost ON tac_stages
    FOR EACH ROW
    EXECUTE FUNCTION update_task_costs();

CREATE TRIGGER update_task_costs_on_helper_change
    AFTER INSERT OR UPDATE OF cost ON tac_helper_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_task_costs();

-- ============================================================================
-- Test Data Insertion Function (For Self-Testing)
-- ============================================================================

CREATE OR REPLACE FUNCTION insert_test_task(
    p_issue_number VARCHAR DEFAULT 'TEST-001'
)
RETURNS UUID AS $$
DECLARE
    v_task_id UUID;
BEGIN
    INSERT INTO tac_tasks (issue_number, status, current_stage, workflow_config, metadata)
    VALUES (
        p_issue_number,
        'running',
        'planning',
        '{"name": "test-workflow", "version": "1.0.0"}'::jsonb,
        '{"test": true}'::jsonb
    )
    RETURNING id INTO v_task_id;

    RAISE NOTICE 'Created test task: %', v_task_id;
    RETURN v_task_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Schema Version
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES (1, 'Initial schema with hybrid architecture support');
