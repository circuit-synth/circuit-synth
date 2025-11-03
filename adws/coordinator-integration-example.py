"""
Example: How to integrate API logging into coordinator.py

Add these imports at top:
    from adw_modules.api_logger import ClaudeAPILogger

Add to Coordinator.__init__():
    self.api_logger = ClaudeAPILogger(LOGS_DIR / 'api')

Modify spawn_worker() to track API calls:
"""

def spawn_worker_with_logging(self, task: Task):
    """Spawn LLM worker agent with API logging (non-blocking)"""

    # Build prompt from template
    template = WORKER_TEMPLATE.read_text()
    prompt = template.format(
        task_id=task.id,
        source=task.source,
        priority=f"p{task.priority}",
        description=task.description,
        worktree_path=str(task.tree_path),
        branch_name=task.branch_name,
        worker_id=task.worker_id,
        issue_number=task.number
    )

    # Write prompt to file
    prompt_file = LOGS_DIR / f"{task.id}-prompt.txt"
    prompt_file.write_text(prompt)

    # Build LLM command from config
    cmd_template = self.config['llm']['command_template']
    model = self.config['llm']['model_default']

    cmd = [
        part.replace('{prompt_file}', str(prompt_file))
            .replace('{model}', model)
        for part in cmd_template
    ]

    # START API LOGGING
    metrics = self.api_logger.start_call(
        task_id=task.id,
        worker_id=task.worker_id,
        model=model,
        prompt_file=str(prompt_file),
        prompt_content=prompt,
        settings={'worktree': str(task.tree_path)}
    )
    # Store metrics reference on task for later
    task.api_metrics = metrics

    print(f"🤖 Spawning worker for {task.id}")
    print(f"   Command: {' '.join(cmd)}")

    # Spawn worker (non-blocking)
    log_file = LOGS_DIR / f"{task.id}.jsonl"
    with open(log_file, 'w') as f:
        proc = subprocess.Popen(
            cmd,
            cwd=task.tree_path,
            stdout=f,
            stderr=subprocess.STDOUT
        )

    self.active_workers[task.worker_id] = proc
    task.pid = proc.pid
    task.started = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"   ✓ Worker {task.worker_id} started (PID: {proc.pid})")


"""
Modify check_completions() to log API results:
"""

def check_completions_with_logging(self, tasks: List[Task]) -> List[Task]:
    """Check if active workers have completed and log API metrics"""

    updated_tasks = []

    for task in tasks:
        if task.status != 'active':
            updated_tasks.append(task)
            continue

        # Check if process still running
        proc = self.active_workers.get(task.worker_id)
        if proc and proc.poll() is None:
            updated_tasks.append(task)
            continue

        print(f"🏁 Worker {task.worker_id} finished for {task.id}")

        # PARSE API USAGE FROM JSONL OUTPUT
        log_file = LOGS_DIR / f"{task.id}.jsonl"
        usage = self.api_logger.parse_stream_json_output(log_file)

        # Check for PR creation (completion)
        # ... existing PR check logic ...

        # COMPLETE API LOGGING
        if hasattr(task, 'api_metrics'):
            self.api_logger.end_call(
                metrics=task.api_metrics,
                response_content=usage['response_content'],
                tokens_input=usage['tokens_input'],
                tokens_output=usage['tokens_output'],
                success=(task.status == 'completed'),
                error_message=task.error,
                exit_code=proc.returncode if proc else None
            )

        updated_tasks.append(task)

    return updated_tasks
