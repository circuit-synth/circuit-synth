// TAC Dashboard Application

const API_BASE = '/api';

// State
let currentView = 'tasks';
let refreshInterval = null;
let modalRefreshInterval = null;
let currentTaskId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    loadStats();
    loadTasks();
    startAutoRefresh();
});

// Navigation
function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const view = item.dataset.view;
            switchView(view);

            // Update active state
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function switchView(view) {
    currentView = view;

    // Hide all views
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));

    // Show selected view
    document.getElementById(`view-${view}`).classList.remove('hidden');

    // Load data for view
    switch(view) {
        case 'tasks':
            loadTasks();
            break;
        case 'active':
            loadActiveTasks();
            break;
        case 'templates':
            loadTemplates();
            break;
        case 'stats':
            loadStats();
            break;
    }
}

// Auto-refresh
function startAutoRefresh() {
    refreshInterval = setInterval(() => {
        loadStats();
        if (currentView === 'tasks') loadTasks();
        if (currentView === 'active') loadActiveTasks();
    }, 5000); // Refresh every 5 seconds
}

// API calls
async function apiGet(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Load Stats
async function loadStats() {
    try {
        const data = await apiGet('/stats');

        document.getElementById('stat-total-tasks').textContent = data.tasks.total;
        document.getElementById('stat-running-tasks').textContent = data.tasks.running;
        document.getElementById('stat-total-cost').textContent = `$${data.costs.total.toFixed(4)}`;
        document.getElementById('stat-total-helpers').textContent = data.helpers.total;

        // If on stats view, show detailed stats
        if (currentView === 'stats') {
            renderDetailedStats(data);
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

function renderDetailedStats(data) {
    const statsGrid = document.getElementById('stats-grid');
    statsGrid.innerHTML = `
        <div class="stats-card">
            <h3>Task Statistics</h3>
            <div class="stats-row">
                <span>Total Tasks</span>
                <strong>${data.tasks.total}</strong>
            </div>
            <div class="stats-row">
                <span>Running</span>
                <strong style="color: var(--primary)">${data.tasks.running}</strong>
            </div>
            <div class="stats-row">
                <span>Completed</span>
                <strong style="color: var(--success)">${data.tasks.completed}</strong>
            </div>
            <div class="stats-row">
                <span>Errored</span>
                <strong style="color: var(--error)">${data.tasks.errored}</strong>
            </div>
        </div>

        <div class="stats-card">
            <h3>Cost & Usage</h3>
            <div class="stats-row">
                <span>Total Cost</span>
                <strong>$${data.costs.total.toFixed(4)}</strong>
            </div>
            <div class="stats-row">
                <span>Input Tokens</span>
                <strong>${data.costs.input_tokens.toLocaleString()}</strong>
            </div>
            <div class="stats-row">
                <span>Output Tokens</span>
                <strong>${data.costs.output_tokens.toLocaleString()}</strong>
            </div>
            <div class="stats-row">
                <span>Avg Cost/Task</span>
                <strong>$${data.tasks.total > 0 ? (data.costs.total / data.tasks.total).toFixed(6) : '0.000000'}</strong>
            </div>
        </div>

        <div class="stats-card">
            <h3>Helper Agents</h3>
            <div class="stats-row">
                <span>Total Helpers</span>
                <strong>${data.helpers.total}</strong>
            </div>
            <div class="stats-row">
                <span>Active Templates</span>
                <strong>${data.templates.active}</strong>
            </div>
            <div class="stats-row">
                <span>Avg Helpers/Task</span>
                <strong>${data.tasks.total > 0 ? (data.helpers.total / data.tasks.total).toFixed(1) : '0.0'}</strong>
            </div>
        </div>
    `;
}

// Load Tasks
async function loadTasks() {
    try {
        const data = await apiGet('/tasks?limit=50');
        renderTaskList(data.tasks, 'task-list');
    } catch (error) {
        document.getElementById('task-list').innerHTML = '<div class="loading">Error loading tasks</div>';
    }
}

// Load Active Tasks
async function loadActiveTasks() {
    try {
        const data = await apiGet('/active');
        renderTaskList(data.tasks, 'active-task-list');
    } catch (error) {
        document.getElementById('active-task-list').innerHTML = '<div class="loading">Error loading active tasks</div>';
    }
}

// Render Task List
function renderTaskList(tasks, containerId) {
    const container = document.getElementById(containerId);

    if (tasks.length === 0) {
        container.innerHTML = '<div class="loading">No tasks found</div>';
        return;
    }

    container.innerHTML = tasks.map(task => `
        <div class="task-card" onclick="showTaskDetail('${task.id}')">
            <div class="task-header">
                <div class="task-title">${task.issue_number}</div>
                <div class="task-status ${task.status}">${task.status}</div>
            </div>

            <div class="task-meta">
                <div class="meta-item">
                    <div class="meta-label">Cost</div>
                    <div class="meta-value">$${task.total_cost ? task.total_cost.toFixed(6) : '0.000000'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Input Tokens</div>
                    <div class="meta-value">${task.total_input_tokens || 0}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Output Tokens</div>
                    <div class="meta-value">${task.total_output_tokens || 0}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Created</div>
                    <div class="meta-value">${formatDateTime(task.created_at)}</div>
                </div>
            </div>
        </div>
    `).join('');
}

// Show Task Detail
async function showTaskDetail(taskId) {
    const modal = document.getElementById('task-modal');
    const modalBody = document.getElementById('modal-body');

    // Store current task ID for refresh
    currentTaskId = taskId;

    // Clear any existing modal refresh interval
    if (modalRefreshInterval) {
        clearInterval(modalRefreshInterval);
    }

    modal.classList.remove('hidden');
    modalBody.innerHTML = '<div class="loading">Loading task details...</div>';

    // Load initial data
    await refreshTaskDetail();

    // Start auto-refresh every 3 seconds for running tasks
    modalRefreshInterval = setInterval(async () => {
        await refreshTaskDetail();
    }, 3000);
}

async function refreshTaskDetail() {
    if (!currentTaskId) return;

    try {
        const data = await apiGet(`/tasks/${currentTaskId}`);
        renderTaskDetail(data);

        // If task is completed or errored, stop refreshing
        if (data.task.status === 'completed' || data.task.status === 'errored') {
            if (modalRefreshInterval) {
                clearInterval(modalRefreshInterval);
                modalRefreshInterval = null;
            }
        }
    } catch (error) {
        const modalBody = document.getElementById('modal-body');
        modalBody.innerHTML = '<div class="loading">Error loading task details</div>';

        // Stop refresh on error
        if (modalRefreshInterval) {
            clearInterval(modalRefreshInterval);
            modalRefreshInterval = null;
        }
    }
}

function closeTaskDetail() {
    document.getElementById('task-modal').classList.add('hidden');

    // Clear modal refresh interval when closing
    if (modalRefreshInterval) {
        clearInterval(modalRefreshInterval);
        modalRefreshInterval = null;
    }
    currentTaskId = null;
}

// Render Task Detail
function renderTaskDetail(data) {
    const { task, stages, helpers, latest_events } = data;

    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');

    // Add refresh indicator for running tasks
    const refreshIndicator = task.status === 'running'
        ? ' <span style="font-size: 0.8em; opacity: 0.7; font-weight: normal;">(auto-updating every 3s)</span>'
        : '';
    modalTitle.innerHTML = `Task: ${task.issue_number}${refreshIndicator}`;

    modalBody.innerHTML = `
        <div class="detail-section">
            <div class="task-header">
                <div class="task-title">
                    <a href="https://github.com/circuit-synth/circuit-synth/issues/${task.issue_number.replace('gh-', '')}"
                       target="_blank"
                       rel="noopener noreferrer"
                       style="color: inherit; text-decoration: none; display: flex; align-items: center; gap: 8px;">
                        ${task.issue_number}
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" style="opacity: 0.6;">
                            <path d="M3.75 2h3.5a.75.75 0 0 1 0 1.5h-3.5a.25.25 0 0 0-.25.25v8.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25v-3.5a.75.75 0 0 1 1.5 0v3.5A1.75 1.75 0 0 1 12.25 14h-8.5A1.75 1.75 0 0 1 2 12.25v-8.5C2 2.784 2.784 2 3.75 2Zm6.854-1h4.146a.25.25 0 0 1 .25.25v4.146a.25.25 0 0 1-.427.177L13.03 4.03 9.28 7.78a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042l3.75-3.75-1.543-1.543A.25.25 0 0 1 10.604 1Z"></path>
                        </svg>
                    </a>
                </div>
                <div class="task-status ${task.status}">${task.status}</div>
            </div>

            <div class="detail-grid">
                <div class="meta-item">
                    <div class="meta-label">Task ID</div>
                    <div class="meta-value" style="font-size: 0.85em; word-break: break-all;">${task.id || 'N/A'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Status</div>
                    <div class="meta-value">${task.status}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Total Cost</div>
                    <div class="meta-value">$${task.total_cost ? task.total_cost.toFixed(6) : '0.000000'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Input Tokens</div>
                    <div class="meta-value">${task.total_input_tokens || 0}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Output Tokens</div>
                    <div class="meta-value">${task.total_output_tokens || 0}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Created</div>
                    <div class="meta-value">${formatDateTime(task.created_at)}</div>
                </div>
            </div>
        </div>

        ${stages.length > 0 ? `
            <div class="detail-section">
                <h3>Stages (${stages.length})</h3>
                <div class="stage-list">
                    ${stages.map(stage => `
                        <div class="stage-item">
                            <div class="helper-name">${stage.stage_name}</div>
                            <div class="task-meta">
                                <div class="meta-item">
                                    <div class="meta-label">Status</div>
                                    <div class="meta-value">${stage.status}</div>
                                </div>
                                <div class="meta-item">
                                    <div class="meta-label">Started</div>
                                    <div class="meta-value">${formatDateTime(stage.start_time)}</div>
                                </div>
                                ${stage.end_time ? `
                                    <div class="meta-item">
                                        <div class="meta-label">Completed</div>
                                        <div class="meta-value">${formatDateTime(stage.end_time)}</div>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}

        ${helpers.length > 0 ? `
            <div class="detail-section">
                <h3>Helper Agents (${helpers.length})</h3>
                <div class="helper-list">
                    ${helpers.map(helper => `
                        <div class="helper-item">
                            <div class="helper-name">${helper.agent_name}</div>
                            <div class="meta-label">Template: ${helper.agent_template}</div>
                            <div class="task-meta">
                                <div class="meta-item">
                                    <div class="meta-label">Status</div>
                                    <div class="meta-value">${helper.status}</div>
                                </div>
                                <div class="meta-item">
                                    <div class="meta-label">Provider</div>
                                    <div class="meta-value">${helper.provider || 'N/A'}</div>
                                </div>
                                <div class="meta-item">
                                    <div class="meta-label">Model</div>
                                    <div class="meta-value">${helper.model || 'N/A'}</div>
                                </div>
                                <div class="meta-item">
                                    <div class="meta-label">Cost</div>
                                    <div class="meta-value">$${helper.cost ? helper.cost.toFixed(6) : '0.000000'}</div>
                                </div>
                                <div class="meta-item">
                                    <div class="meta-label">Input Tokens</div>
                                    <div class="meta-value">${helper.input_tokens || 0}</div>
                                </div>
                                <div class="meta-item">
                                    <div class="meta-label">Output Tokens</div>
                                    <div class="meta-value">${helper.output_tokens || 0}</div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}

        ${latest_events.length > 0 ? `
            <div class="detail-section">
                <h3>Recent Events</h3>
                <div class="helper-list">
                    ${latest_events.map(event => `
                        <div class="helper-item">
                            <div class="helper-name">${event.event_type}</div>
                            ${event.summary ? `<div class="meta-label">${event.summary}</div>` : ''}
                            <div class="task-meta">
                                <div class="meta-item">
                                    <div class="meta-label">Category</div>
                                    <div class="meta-value">${event.event_category}</div>
                                </div>
                                <div class="meta-item">
                                    <div class="meta-label">Time</div>
                                    <div class="meta-value">${formatDateTime(event.timestamp)}</div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}
    `;
}

// Load Templates
async function loadTemplates() {
    try {
        const data = await apiGet('/templates');
        renderTemplateList(data.templates);
    } catch (error) {
        document.getElementById('template-list').innerHTML = '<div class="loading">Error loading templates</div>';
    }
}

function renderTemplateList(templates) {
    const container = document.getElementById('template-list');

    if (templates.length === 0) {
        container.innerHTML = '<div class="loading">No templates found</div>';
        return;
    }

    container.innerHTML = templates.map(template => `
        <div class="template-card">
            <div class="task-header">
                <div class="task-title">${template.name}</div>
                <div class="task-status ${template.is_active ? 'completed' : ''}">${template.is_active ? 'active' : 'inactive'}</div>
            </div>

            ${template.description ? `<p style="margin: 0.5rem 0; color: var(--gray-600);">${template.description}</p>` : ''}

            <div class="task-meta">
                <div class="meta-item">
                    <div class="meta-label">Model</div>
                    <div class="meta-value">${template.model || 'N/A'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Temperature</div>
                    <div class="meta-value">${template.temperature !== null ? template.temperature : 'N/A'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Color</div>
                    <div class="meta-value">${template.color || 'N/A'}</div>
                </div>
            </div>
        </div>
    `).join('');
}

// Utilities
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Conversations View
let selectedConversationId = null;

async function loadConversations() {
    try {
        // For now, we'll load conversations from helper agents and events
        const helpers = await apiGet('/helpers');  // Will need this endpoint
        renderConversationsList(helpers || []);
    } catch (error) {
        document.getElementById('conversations-sidebar').innerHTML = 
            '<div class="loading">No conversations available yet</div>';
    }
}

function renderConversationsList(conversations) {
    const sidebar = document.getElementById('conversations-sidebar');
    
    if (conversations.length === 0) {
        sidebar.innerHTML = `
            <div class="empty-state">
                <p>No conversations yet</p>
                <p style="font-size: 0.9em; margin-top: 0.5rem;">
                    Conversations will appear here when agents start working on tasks
                </p>
            </div>
        `;
        return;
    }

    sidebar.innerHTML = conversations.map(conv => `
        <div class="conversation-item ${selectedConversationId === conv.id ? 'active' : ''}"
             onclick="selectConversation('${conv.id}')">
            <div class="conversation-header">
                <div class="conversation-agent">${conv.agent_name}</div>
                <div class="task-status ${conv.status}">${conv.status}</div>
            </div>
            <div class="conversation-meta">
                <span>Task: ${conv.task_id}</span>
                <span>Tokens: ${conv.input_tokens + conv.output_tokens}</span>
                <span>Cost: $${conv.total_cost ? conv.total_cost.toFixed(6) : '0.000000'}</span>
            </div>
        </div>
    `).join('');
}

async function selectConversation(conversationId) {
    selectedConversationId = conversationId;

    // Reload list to update active state
    loadConversations();

    // Load conversation details
    const detailContainer = document.getElementById('conversation-detail');
    detailContainer.innerHTML = '<div class="loading">Loading conversation...</div>';

    try {
        const conversation = await apiGet(`/conversations/${conversationId}`);
        renderConversationDetail(conversation);
    } catch (error) {
        detailContainer.innerHTML = '<div class="loading">Error loading conversation</div>';
    }
}

function renderConversationDetail(conversation) {
    const detailContainer = document.getElementById('conversation-detail');

    detailContainer.innerHTML = `
        <div class="detail-section">
            <h3>${conversation.agent_name}</h3>
            <div class="detail-grid">
                <div class="meta-item">
                    <div class="meta-label">Status</div>
                    <div class="meta-value">${conversation.status}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Model</div>
                    <div class="meta-value">${conversation.model || 'N/A'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Provider</div>
                    <div class="meta-value">${conversation.provider || 'N/A'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Total Cost</div>
                    <div class="meta-value">$${conversation.total_cost ? conversation.total_cost.toFixed(6) : '0.000000'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Input Tokens</div>
                    <div class="meta-value">${conversation.input_tokens || 0}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Output Tokens</div>
                    <div class="meta-value">${conversation.output_tokens || 0}</div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h3>Messages (${conversation.messages ? conversation.messages.length : 0})</h3>
            <div class="conversation-messages">
                ${renderMessages(conversation.messages || [])}
            </div>
        </div>
    `;
}

function renderMessages(messages, depth = 0) {
    if (!messages || messages.length === 0) {
        return '<div class="empty-state">No messages yet</div>';
    }

    return messages.map(msg => `
        <div class="message ${msg.role}" style="margin-left: ${depth * 2}rem;">
            <div class="message-header">
                <span class="message-role">${msg.role}</span>
                <span class="message-timestamp">${formatDateTime(msg.timestamp)}</span>
            </div>
            <div class="message-content">${escapeHtml(msg.content)}</div>
            ${msg.input_tokens || msg.output_tokens ? `
                <div class="message-tokens">
                    ${msg.input_tokens ? `<span>In: ${msg.input_tokens}</span>` : ''}
                    ${msg.output_tokens ? `<span>Out: ${msg.output_tokens}</span>` : ''}
                    ${msg.cost ? `<span>Cost: $${msg.cost.toFixed(6)}</span>` : ''}
                </div>
            ` : ''}
            ${msg.nested_conversations ? `
                <div class="nested-conversation">
                    <div class="nested-indicator">↳ Nested Helper Agent</div>
                    ${renderMessages(msg.nested_conversations, depth + 1)}
                </div>
            ` : ''}
        </div>
    `).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
