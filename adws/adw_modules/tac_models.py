#!/usr/bin/env python3
"""
TAC-X Pydantic Models

Type-safe data models for TAC database records.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field


class TaskModel(BaseModel):
    """TAC task model"""
    id: UUID
    issue_number: str
    status: str  # running, completed, errored, blocked, cancelled
    current_stage: Optional[str] = None  # planning, building, reviewing, pr_creation
    workflow_config: Optional[Dict[str, Any]] = None
    worktree_path: Optional[str] = None
    branch_name: Optional[str] = None
    total_cost: Decimal = Decimal("0")
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True  # Allows creating from asyncpg Record


class StageModel(BaseModel):
    """TAC stage model"""
    id: UUID
    task_id: UUID
    stage_name: str  # planning, building, reviewing, pr_creation
    status: str  # pending, running, completed, errored, skipped
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[Decimal] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: Decimal = Decimal("0")
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class HelperAgentModel(BaseModel):
    """TAC helper agent model"""
    id: UUID
    task_id: UUID
    stage_id: Optional[UUID] = None
    agent_name: str
    agent_template: str
    status: str  # running, completed, errored, interrupted
    provider: Optional[str] = None
    model: Optional[str] = None
    session_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: Decimal = Decimal("0")
    result_summary: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class EventModel(BaseModel):
    """TAC event model"""
    id: UUID
    task_id: UUID
    stage_id: Optional[UUID] = None
    helper_agent_id: Optional[UUID] = None
    event_category: str  # stage, helper, hook, system, coordinator
    event_type: str
    content: Optional[str] = None
    summary: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class AgentTemplateModel(BaseModel):
    """TAC agent template model"""
    id: UUID
    name: str
    description: Optional[str] = None
    system_prompt: str
    tools: List[str] = Field(default_factory=list)
    model: str = "sonnet"
    temperature: Decimal = Decimal("1.0")
    color: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class CostSummaryModel(BaseModel):
    """TAC cost summary model"""
    id: UUID
    task_id: UUID
    date: datetime
    total_cost: Decimal = Decimal("0")
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    stage_costs: Optional[Dict[str, Any]] = None
    helper_costs: Optional[Dict[str, Any]] = None
    updated_at: datetime

    class Config:
        from_attributes = True


# Simplified models for creation (input)

class TaskCreate(BaseModel):
    """Model for creating a new task"""
    issue_number: str
    workflow_config: Optional[Dict[str, Any]] = None
    worktree_path: Optional[str] = None
    branch_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class StageCreate(BaseModel):
    """Model for creating a new stage"""
    task_id: UUID
    stage_name: str
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None


class HelperAgentCreate(BaseModel):
    """Model for creating a helper agent"""
    task_id: UUID
    stage_id: Optional[UUID] = None
    agent_name: str
    agent_template: str
    provider: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EventCreate(BaseModel):
    """Model for creating an event"""
    task_id: UUID
    stage_id: Optional[UUID] = None
    helper_agent_id: Optional[UUID] = None
    event_category: str
    event_type: str
    content: Optional[str] = None
    summary: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


# Response models (with aggregated data)

class TaskSummary(BaseModel):
    """Task with aggregated stages and helpers"""
    task: TaskModel
    stages: List[StageModel] = Field(default_factory=list)
    helpers: List[HelperAgentModel] = Field(default_factory=list)
    event_count: int = 0
    latest_events: List[EventModel] = Field(default_factory=list)


class StageWithEvents(BaseModel):
    """Stage with its events"""
    stage: StageModel
    events: List[EventModel] = Field(default_factory=list)


class HelperWithEvents(BaseModel):
    """Helper agent with its events"""
    helper: HelperAgentModel
    events: List[EventModel] = Field(default_factory=list)
