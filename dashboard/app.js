// TAC Dashboard Application

const API_BASE = 'http://localhost:8001/api';

// State
let currentView = 'tasks';
let refreshInterval = null;

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
        <div class="task-card" onclick="showTaskDetail('${task.task_id}')">
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

    modal.classList.remove('hidden');
    modalBody.innerHTML = '<div class="loading">Loading task details...</div>';

    try {
        const data = await apiGet(`/tasks/${taskId}`);
        renderTaskDetail(data);
    } catch (error) {
        modalBody.innerHTML = '<div class="loading">Error loading task details</div>';
    }
}

function closeTaskDetail() {
    document.getElementById('task-modal').classList.add('hidden');
}

// Render Task Detail
function renderTaskDetail(data) {
    const { task, stages, helpers, latest_events } = data;

    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');

    modalTitle.textContent = `Task: ${task.issue_number}`;

    modalBody.innerHTML = `
        <div class="detail-section">
            <div class="task-header">
                <div class="task-title">${task.issue_number}</div>
                <div class="task-status ${task.status}">${task.status}</div>
            </div>

            <div class="detail-grid">
                <div class="meta-item">
                    <div class="meta-label">Task ID</div>
                    <div class="meta-value">${task.task_id}</div>
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
