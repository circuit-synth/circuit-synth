"""
Core Circuit Debugging Analysis Engine

Provides the main CircuitDebugger class for analyzing circuit issues
and managing debugging sessions.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class DebugCategory(Enum):
    """Categories of circuit debugging issues"""
    POWER = "power"
    DIGITAL = "digital"
    ANALOG = "analog"
    RF = "rf"
    THERMAL = "thermal"
    MECHANICAL = "mechanical"
    MANUFACTURING = "manufacturing"
    SOFTWARE = "software"


class IssueSeverity(Enum):
    """Severity levels for identified issues"""
    CRITICAL = "critical"  # Board won't function at all
    HIGH = "high"         # Major functionality impaired
    MEDIUM = "medium"     # Some features affected
    LOW = "low"          # Minor issues or optimizations


@dataclass
class DebugIssue:
    """Represents a potential issue identified during debugging"""
    category: DebugCategory
    severity: IssueSeverity
    title: str
    description: str
    symptoms: List[str]
    probable_causes: List[str]
    test_suggestions: List[str]
    solutions: List[str]
    confidence: float  # 0.0 to 1.0
    related_components: List[str] = field(default_factory=list)
    reference_designs: List[str] = field(default_factory=list)


@dataclass
class DebugSession:
    """Manages a complete debugging session"""
    session_id: str
    board_name: str
    board_version: str
    started_at: datetime
    symptoms: List[str] = field(default_factory=list)
    measurements: Dict[str, Any] = field(default_factory=dict)
    observations: List[str] = field(default_factory=list)
    identified_issues: List[DebugIssue] = field(default_factory=list)
    test_history: List[Dict[str, Any]] = field(default_factory=list)
    resolution: Optional[str] = None
    root_cause: Optional[str] = None
    ended_at: Optional[datetime] = None
    
    def add_symptom(self, symptom: str):
        """Add a symptom description"""
        self.symptoms.append(symptom)
        logger.info(f"Added symptom: {symptom}")
    
    def add_measurement(self, name: str, value: Any, unit: str = "", notes: str = ""):
        """Add a test measurement"""
        self.measurements[name] = {
            "value": value,
            "unit": unit,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Added measurement: {name} = {value}{unit}")
    
    def add_observation(self, observation: str):
        """Add a general observation"""
        self.observations.append({
            "text": observation,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Added observation: {observation}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "board_name": self.board_name,
            "board_version": self.board_version,
            "started_at": self.started_at.isoformat(),
            "symptoms": self.symptoms,
            "measurements": self.measurements,
            "observations": self.observations,
            "identified_issues": [
                {
                    "category": issue.category.value,
                    "severity": issue.severity.value,
                    "title": issue.title,
                    "description": issue.description,
                    "symptoms": issue.symptoms,
                    "probable_causes": issue.probable_causes,
                    "test_suggestions": issue.test_suggestions,
                    "solutions": issue.solutions,
                    "confidence": issue.confidence,
                    "related_components": issue.related_components,
                    "reference_designs": issue.reference_designs
                }
                for issue in self.identified_issues
            ],
            "test_history": self.test_history,
            "resolution": self.resolution,
            "root_cause": self.root_cause,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None
        }


class CircuitDebugger:
    """Main circuit debugging analysis engine"""
    
    def __init__(self, knowledge_base_path: Optional[Path] = None):
        """Initialize the debugger with optional knowledge base"""
        self.knowledge_base_path = knowledge_base_path or Path("memory-bank/debugging")
        self.active_sessions: Dict[str, DebugSession] = {}
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load debugging patterns and historical data"""
        self.known_patterns = []
        self.component_failures = {}
        self.successful_resolutions = []
        
        if self.knowledge_base_path.exists():
            # Load historical debugging data
            patterns_file = self.knowledge_base_path / "patterns.json"
            if patterns_file.exists():
                with open(patterns_file) as f:
                    self.known_patterns = json.load(f)
            
            # Load component failure database
            failures_file = self.knowledge_base_path / "component_failures.json"
            if failures_file.exists():
                with open(failures_file) as f:
                    self.component_failures = json.load(f)
    
    def start_session(self, board_name: str, board_version: str = "1.0") -> DebugSession:
        """Start a new debugging session"""
        from uuid import uuid4
        
        session = DebugSession(
            session_id=str(uuid4()),
            board_name=board_name,
            board_version=board_version,
            started_at=datetime.now()
        )
        
        self.active_sessions[session.session_id] = session
        logger.info(f"Started debugging session {session.session_id} for {board_name} v{board_version}")
        return session
    
    def analyze_power_issue(self, session: DebugSession) -> List[DebugIssue]:
        """Analyze power-related issues based on symptoms and measurements"""
        issues = []
        
        # Check for common power issues
        if any("not turning on" in s.lower() for s in session.symptoms):
            issue = DebugIssue(
                category=DebugCategory.POWER,
                severity=IssueSeverity.CRITICAL,
                title="Board Not Powering On",
                description="The board is not showing any signs of power",
                symptoms=["No LEDs", "No voltage on power rails", "No current draw"],
                probable_causes=[
                    "Input power not connected or incorrect voltage",
                    "Power switch or enable pin not activated",
                    "Short circuit on power rail",
                    "Damaged voltage regulator",
                    "Incorrect component orientation (diode/regulator)",
                    "PCB manufacturing defect (open trace)"
                ],
                test_suggestions=[
                    "Measure input voltage at power connector",
                    "Check continuity from input to regulator",
                    "Measure resistance between power rails and ground",
                    "Verify regulator enable pin state",
                    "Use thermal camera to identify hot spots"
                ],
                solutions=[
                    "Verify correct input voltage and polarity",
                    "Check and replace fuse if present",
                    "Inspect for solder bridges or shorts",
                    "Replace voltage regulator if damaged",
                    "Reflow solder joints on power components"
                ],
                confidence=0.85,
                related_components=["U1 (Voltage Regulator)", "F1 (Fuse)", "D1 (Protection Diode)"]
            )
            issues.append(issue)
        
        # Check for voltage regulation issues
        for name, data in session.measurements.items():
            if "voltage" in name.lower() or name.endswith("V"):
                voltage = float(data.get("value", 0))
                
                # Check for 3.3V rail issues
                if "3.3" in name or "3V3" in name:
                    if voltage < 3.0 or voltage > 3.6:
                        issue = DebugIssue(
                            category=DebugCategory.POWER,
                            severity=IssueSeverity.HIGH,
                            title=f"3.3V Rail Out of Specification ({voltage}V)",
                            description=f"The 3.3V power rail is measuring {voltage}V, outside acceptable range",
                            symptoms=[f"Measured {voltage}V on 3.3V rail"],
                            probable_causes=[
                                "Overloaded regulator (too much current draw)",
                                "Incorrect feedback resistor values",
                                "Damaged regulator IC",
                                "Insufficient input voltage",
                                "Poor PCB layout causing voltage drop"
                            ],
                            test_suggestions=[
                                "Measure current draw on 3.3V rail",
                                "Check regulator input voltage",
                                "Verify feedback resistor values",
                                "Monitor voltage while disconnecting loads",
                                "Check regulator temperature"
                            ],
                            solutions=[
                                "Reduce load on regulator",
                                "Add additional bulk capacitance",
                                "Improve PCB power trace routing",
                                "Replace regulator with higher current rating",
                                "Fix feedback network resistor values"
                            ],
                            confidence=0.9,
                            related_components=["Voltage Regulator", "Feedback Resistors", "Output Capacitors"]
                        )
                        issues.append(issue)
        
        return issues
    
    def analyze_digital_communication(self, session: DebugSession) -> List[DebugIssue]:
        """Analyze digital communication issues (I2C, SPI, UART, etc.)"""
        issues = []
        
        # Check for I2C issues
        if any("i2c" in s.lower() for s in session.symptoms):
            issue = DebugIssue(
                category=DebugCategory.DIGITAL,
                severity=IssueSeverity.HIGH,
                title="I2C Communication Failure",
                description="I2C communication is not working between devices",
                symptoms=["No ACK from slave device", "SDA/SCL stuck low or high", "Intermittent communication"],
                probable_causes=[
                    "Missing or incorrect pull-up resistors",
                    "Wrong I2C address",
                    "Voltage level mismatch between devices",
                    "Clock stretching timeout",
                    "Bus capacitance too high",
                    "Ground loop or poor ground connection"
                ],
                test_suggestions=[
                    "Measure voltage levels on SDA and SCL",
                    "Check pull-up resistor values (typically 2.2k-10k)",
                    "Verify I2C address with scanner tool",
                    "Monitor bus with logic analyzer",
                    "Check rise/fall times with oscilloscope"
                ],
                solutions=[
                    "Add or adjust pull-up resistors",
                    "Implement level shifter if voltage mismatch",
                    "Reduce I2C clock speed",
                    "Shorten trace lengths or add buffer",
                    "Fix ground connections between devices"
                ],
                confidence=0.8,
                related_components=["I2C Pull-up Resistors", "Level Shifters", "I2C Devices"]
            )
            issues.append(issue)
        
        # Check for USB issues
        if any("usb" in s.lower() for s in session.symptoms):
            issue = DebugIssue(
                category=DebugCategory.DIGITAL,
                severity=IssueSeverity.HIGH,
                title="USB Enumeration Failure",
                description="USB device is not being recognized by the host",
                symptoms=["Device not detected", "Enumeration fails", "Device disconnect/reconnect loop"],
                probable_causes=[
                    "Incorrect D+/D- routing or connection",
                    "Missing or incorrect termination resistors",
                    "Crystal frequency incorrect or not oscillating",
                    "USB power negotiation failure",
                    "Firmware USB stack issues",
                    "ESD damage to USB transceiver"
                ],
                test_suggestions=[
                    "Measure VBUS voltage (should be 5V)",
                    "Check D+ and D- signal integrity with scope",
                    "Verify crystal oscillation frequency",
                    "Monitor USB packets with analyzer",
                    "Test with different USB cables and ports"
                ],
                solutions=[
                    "Fix D+/D- trace routing (match lengths, impedance)",
                    "Add proper crystal load capacitors",
                    "Implement USB termination per spec",
                    "Add ESD protection diodes",
                    "Update USB firmware/drivers"
                ],
                confidence=0.85,
                related_components=["USB Connector", "Crystal", "USB Transceiver", "ESD Protection"]
            )
            issues.append(issue)
        
        return issues
    
    def analyze_symptoms(self, session: DebugSession) -> List[DebugIssue]:
        """Main analysis function that routes to specific analyzers"""
        all_issues = []
        
        # Analyze based on symptom categories
        symptom_text = " ".join(session.symptoms).lower()
        
        if any(word in symptom_text for word in ["power", "voltage", "current", "hot", "burning"]):
            all_issues.extend(self.analyze_power_issue(session))
        
        if any(word in symptom_text for word in ["i2c", "spi", "uart", "usb", "can", "communication"]):
            all_issues.extend(self.analyze_digital_communication(session))
        
        # Sort by severity and confidence
        all_issues.sort(key=lambda x: (x.severity.value, -x.confidence))
        
        # Update session with identified issues
        session.identified_issues = all_issues
        
        return all_issues
    
    def suggest_next_test(self, session: DebugSession) -> List[str]:
        """Suggest the next debugging step based on current state"""
        suggestions = []
        
        if not session.measurements:
            suggestions.append("Start with basic power measurements: VBUS, VCC, GND continuity")
        
        if session.identified_issues:
            # Get test suggestions from highest priority issue
            top_issue = session.identified_issues[0]
            suggestions.extend(top_issue.test_suggestions[:3])
        
        return suggestions
    
    def close_session(self, session: DebugSession, resolution: str, root_cause: str):
        """Close a debugging session with resolution"""
        session.resolution = resolution
        session.root_cause = root_cause
        session.ended_at = datetime.now()
        
        # Save to knowledge base
        self._save_session_to_knowledge_base(session)
        
        # Remove from active sessions
        if session.session_id in self.active_sessions:
            del self.active_sessions[session.session_id]
        
        logger.info(f"Closed debugging session {session.session_id}: {root_cause}")
    
    def _save_session_to_knowledge_base(self, session: DebugSession):
        """Save debugging session to knowledge base for future reference"""
        if not self.knowledge_base_path.exists():
            self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        
        # Save session data
        session_file = self.knowledge_base_path / f"session_{session.session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
        
        logger.info(f"Saved debugging session to {session_file}")