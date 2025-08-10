#!/usr/bin/env python3
"""
Circuit Generation Workflow Logging System

Provides comprehensive logging infrastructure for all agents in the circuit generation workflow.
Creates timestamped markdown logs with structured sections for complete transparency.
"""

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AgentExecutionLog:
    """Structure for individual agent execution records"""

    agent_name: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str  # "running", "completed", "failed"
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    decision_log: List[str]
    error_messages: List[str]
    duration_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with ISO datetime formatting"""
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        return data


class CircuitWorkflowLogger:
    """Master logging system for circuit generation workflow"""

    def __init__(self, project_name: str, base_log_dir: str = "logs"):
        self.project_name = project_name
        self.session_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now()

        # Create timestamped log directory
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path(base_log_dir) / timestamp
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Master workflow log
        self.workflow_log = {
            "project_name": project_name,
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "agents_executed": [],
            "total_duration_seconds": None,
            "final_status": "running",
            "user_prompt": None,
            "validation_attempts": [],
            "component_selections": {},
            "design_decisions": [],
        }

        # Agent execution tracking
        self.agent_logs: Dict[str, AgentExecutionLog] = {}
        self.current_agent: Optional[str] = None

        # Create master workflow log file
        self.master_log_file = self.log_dir / f"workflow_{self.session_id}.json"

        print(f"📝 Logging initialized: {self.log_dir}")

    def set_user_prompt(self, prompt: str):
        """Set the original user prompt for the workflow"""
        self.workflow_log["user_prompt"] = prompt
        self._save_workflow_log()

    def start_agent_execution(self, agent_name: str, inputs: Dict[str, Any]) -> str:
        """Start tracking an agent execution"""
        agent_session_id = f"{agent_name}_{str(uuid.uuid4())[:8]}"

        agent_log = AgentExecutionLog(
            agent_name=agent_name,
            session_id=agent_session_id,
            start_time=datetime.now(),
            end_time=None,
            status="running",
            inputs=inputs,
            outputs={},
            decision_log=[],
            error_messages=[],
        )

        self.agent_logs[agent_session_id] = agent_log
        self.current_agent = agent_session_id

        # Create individual agent log file
        self._create_agent_log_file(agent_log)

        print(f"▶️  Started {agent_name} (session: {agent_session_id})")
        return agent_session_id

    def log_agent_decision(self, agent_session_id: str, decision: str, rationale: str):
        """Log a decision made by an agent"""
        if agent_session_id in self.agent_logs:
            timestamp = datetime.now().strftime("%H:%M:%S")
            decision_entry = f"[{timestamp}] **{decision}**: {rationale}"
            self.agent_logs[agent_session_id].decision_log.append(decision_entry)
            self._update_agent_log_file(agent_session_id)

            # Also add to workflow-level decisions
            self.workflow_log["design_decisions"].append(
                {
                    "agent": self.agent_logs[agent_session_id].agent_name,
                    "timestamp": timestamp,
                    "decision": decision,
                    "rationale": rationale,
                }
            )

    def log_component_selection(
        self,
        agent_session_id: str,
        component_type: str,
        selected_part: str,
        alternatives: List[str],
        rationale: str,
    ):
        """Log component selection with alternatives considered"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Log as agent decision
        self.log_agent_decision(
            agent_session_id,
            f"Selected {component_type}: {selected_part}",
            f"{rationale}. Alternatives considered: {', '.join(alternatives) if alternatives else 'None'}",
        )

        # Add to workflow-level component selections
        self.workflow_log["component_selections"][component_type] = {
            "selected": selected_part,
            "alternatives": alternatives,
            "rationale": rationale,
            "timestamp": timestamp,
            "agent": self.agent_logs[agent_session_id].agent_name,
        }
        self._save_workflow_log()

    def log_validation_attempt(
        self, attempt_number: int, success: bool, errors: List[str]
    ):
        """Log a validation attempt and its results"""
        validation_log = {
            "attempt": attempt_number,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "errors": errors,
            "error_count": len(errors),
        }

        self.workflow_log["validation_attempts"].append(validation_log)
        self._save_workflow_log()

        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"🧪 Validation attempt {attempt_number}: {status}")
        if not success:
            print(f"   Errors: {len(errors)}")

    def complete_agent_execution(
        self,
        agent_session_id: str,
        success: bool,
        outputs: Dict[str, Any],
        error_message: str = None,
    ):
        """Complete an agent execution and finalize its log"""
        if agent_session_id in self.agent_logs:
            agent_log = self.agent_logs[agent_session_id]
            agent_log.end_time = datetime.now()
            agent_log.duration_seconds = (
                agent_log.end_time - agent_log.start_time
            ).total_seconds()
            agent_log.status = "completed" if success else "failed"
            agent_log.outputs = outputs

            if error_message:
                agent_log.error_messages.append(error_message)

            # Finalize agent log file
            self._finalize_agent_log_file(agent_log)

            # Add to workflow log
            self.workflow_log["agents_executed"].append(agent_log.to_dict())
            self._save_workflow_log()

            status = "✅" if success else "❌"
            print(
                f"{status} Completed {agent_log.agent_name} ({agent_log.duration_seconds:.1f}s)"
            )

    def finalize_workflow(self, success: bool, final_project_path: str = None):
        """Finalize the entire workflow logging"""
        end_time = datetime.now()
        self.workflow_log["end_time"] = end_time.isoformat()
        self.workflow_log["total_duration_seconds"] = (
            end_time - self.start_time
        ).total_seconds()
        self.workflow_log["final_status"] = "completed" if success else "failed"

        if final_project_path:
            self.workflow_log["final_project_path"] = final_project_path

        self._save_workflow_log()
        self._create_workflow_summary()

        status = "🎉 SUCCESS" if success else "⚠️ FAILED"
        duration = self.workflow_log["total_duration_seconds"]
        print(f"{status} Workflow completed in {duration:.1f}s")
        print(f"📁 Complete logs: {self.log_dir}")

    def _create_agent_log_file(self, agent_log: AgentExecutionLog):
        """Create individual markdown log file for an agent"""
        log_file = self.log_dir / f"{agent_log.agent_name}_{agent_log.session_id}.md"

        content = f"""# {agent_log.agent_name} Execution Log

**Session ID:** {agent_log.session_id}  
**Start Time:** {agent_log.start_time.strftime('%Y-%m-%d %H:%M:%S')}  
**Status:** {agent_log.status.upper()}  

## Input Parameters
```json
{json.dumps(agent_log.inputs, indent=2)}
```

## Execution Log
*Real-time decision log will be updated below...*

## Decision History
"""

        with open(log_file, "w") as f:
            f.write(content)

    def _update_agent_log_file(self, agent_session_id: str):
        """Update the agent log file with latest decisions"""
        agent_log = self.agent_logs[agent_session_id]
        log_file = self.log_dir / f"{agent_log.agent_name}_{agent_log.session_id}.md"

        # Read existing content up to "## Decision History"
        with open(log_file, "r") as f:
            lines = f.readlines()

        # Find the decision history section and replace it
        decision_section_start = None
        for i, line in enumerate(lines):
            if "## Decision History" in line:
                decision_section_start = i + 1
                break

        if decision_section_start is not None:
            # Keep everything up to decision history, then add latest decisions
            updated_content = "".join(lines[:decision_section_start])

            for decision in agent_log.decision_log:
                updated_content += f"\n{decision}\n"

            # Add error section if there are errors
            if agent_log.error_messages:
                updated_content += "\n## Errors Encountered\n"
                for error in agent_log.error_messages:
                    updated_content += f"\n❌ {error}\n"

            with open(log_file, "w") as f:
                f.write(updated_content)

    def _finalize_agent_log_file(self, agent_log: AgentExecutionLog):
        """Finalize agent log with completion status and outputs"""
        log_file = self.log_dir / f"{agent_log.agent_name}_{agent_log.session_id}.md"

        # Update header with final status
        with open(log_file, "r") as f:
            content = f.read()

        # Update status in header
        content = content.replace(
            f"**Status:** RUNNING", f"**Status:** {agent_log.status.upper()}"
        )

        # Add completion details
        completion_section = f"""
**End Time:** {agent_log.end_time.strftime('%Y-%m-%d %H:%M:%S')}  
**Duration:** {agent_log.duration_seconds:.1f} seconds  

## Output Results
```json
{json.dumps(agent_log.outputs, indent=2)}
```

## Execution Summary
- **Total Decisions:** {len(agent_log.decision_log)}
- **Errors:** {len(agent_log.error_messages)}
- **Status:** {agent_log.status.upper()}
"""

        # Insert completion section after the input parameters
        content = content.replace(
            "## Execution Log", completion_section + "\n## Execution Log"
        )

        with open(log_file, "w") as f:
            f.write(content)

    def _save_workflow_log(self):
        """Save the master workflow log"""
        with open(self.master_log_file, "w") as f:
            json.dump(self.workflow_log, f, indent=2)

    def _create_workflow_summary(self):
        """Create a human-readable workflow summary"""
        summary_file = self.log_dir / "workflow_summary.md"

        # Calculate stats
        total_agents = len(self.workflow_log["agents_executed"])
        successful_agents = sum(
            1
            for agent in self.workflow_log["agents_executed"]
            if agent["status"] == "completed"
        )
        total_decisions = len(self.workflow_log["design_decisions"])
        validation_attempts = len(self.workflow_log["validation_attempts"])
        final_validation_success = (
            self.workflow_log["validation_attempts"][-1]["success"]
            if self.workflow_log["validation_attempts"]
            else False
        )

        content = f"""# Circuit Generation Workflow Summary

**Project:** {self.workflow_log["project_name"]}  
**Session ID:** {self.workflow_log["session_id"]}  
**Duration:** {self.workflow_log["total_duration_seconds"]:.1f} seconds  
**Final Status:** {self.workflow_log["final_status"].upper()}  

## User Request
```
{self.workflow_log["user_prompt"] or "Not recorded"}
```

## Execution Statistics
- **Agents Executed:** {total_agents}
- **Successful Agents:** {successful_agents}/{total_agents}
- **Design Decisions:** {total_decisions}
- **Validation Attempts:** {validation_attempts}
- **Final Validation:** {"✅ PASSED" if final_validation_success else "❌ FAILED"}

## Component Selections
"""

        # Add component selections
        for comp_type, selection in self.workflow_log["component_selections"].items():
            content += f"""
### {comp_type}
- **Selected:** {selection["selected"]}
- **Rationale:** {selection["rationale"]}
- **Agent:** {selection["agent"]}
- **Alternatives Considered:** {", ".join(selection["alternatives"]) if selection["alternatives"] else "None"}
"""

        # Add agent execution timeline
        content += "\n## Agent Execution Timeline\n"
        for agent in self.workflow_log["agents_executed"]:
            status_icon = "✅" if agent["status"] == "completed" else "❌"
            content += f"- {status_icon} **{agent['agent_name']}** ({agent.get('duration_seconds', 0):.1f}s)\n"

        # Add validation history
        if self.workflow_log["validation_attempts"]:
            content += "\n## Validation History\n"
            for i, attempt in enumerate(self.workflow_log["validation_attempts"], 1):
                status = (
                    "✅ PASSED"
                    if attempt["success"]
                    else f"❌ FAILED ({attempt['error_count']} errors)"
                )
                content += f"- **Attempt {i}:** {status}\n"

        # Add decision log
        content += "\n## Design Decision Log\n"
        for decision in self.workflow_log["design_decisions"]:
            content += f"- **[{decision['timestamp']}]** {decision['agent']}: {decision['decision']}\n"
            content += f"  - {decision['rationale']}\n"

        with open(summary_file, "w") as f:
            f.write(content)


# Convenience functions for agent integration
def create_workflow_logger(
    project_name: str, user_prompt: str
) -> CircuitWorkflowLogger:
    """Create and initialize a workflow logger"""
    logger = CircuitWorkflowLogger(project_name)
    logger.set_user_prompt(user_prompt)
    return logger


def setup_agent_logging(
    logger: CircuitWorkflowLogger, agent_name: str, inputs: Dict[str, Any]
) -> str:
    """Setup logging for a specific agent execution"""
    return logger.start_agent_execution(agent_name, inputs)


# Example usage for agents
if __name__ == "__main__":
    # Example workflow logging
    logger = create_workflow_logger(
        "test_stm32_imu_board", "Make a PCB with STM32 and 3 IMUs on SPI"
    )

    # Example agent execution
    agent_session = setup_agent_logging(
        logger,
        "stm32-mcu-finder",
        {
            "requirements": "STM32 with 3 SPI peripherals",
            "availability_check": "JLCPCB",
        },
    )

    logger.log_component_selection(
        agent_session,
        "Microcontroller",
        "STM32F407VET6",
        ["STM32F411CEU6", "STM32G431CBT6"],
        "Selected for 3 SPI peripherals and good JLCPCB availability",
    )

    logger.complete_agent_execution(
        agent_session,
        True,
        {
            "selected_mcu": "STM32F407VET6",
            "jlcpcb_part": "C116735",
            "stock_count": 1247,
        },
    )

    # Example validation
    logger.log_validation_attempt(1, False, ["Net creation outside circuit context"])
    logger.log_validation_attempt(2, True, [])

    logger.finalize_workflow(True, "/path/to/generated/project")

    print("Example logging completed. Check logs/ directory for output.")
