"""
Debugging Knowledge Base and Pattern Recognition

Manages historical debugging data, known failure patterns, and
component-specific failure modes.
"""

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DebugPattern:
    """Represents a known debugging pattern from historical data"""

    pattern_id: str
    category: str
    symptoms: List[str]
    root_cause: str
    solutions: List[str]
    component_types: List[str]
    occurrence_count: int = 1
    success_rate: float = 1.0
    typical_measurements: Dict[str, Any] = None
    references: List[str] = None

    def matches_symptoms(self, symptoms: List[str], threshold: float = 0.5) -> float:
        """Calculate similarity between pattern and given symptoms"""
        if not self.symptoms or not symptoms:
            return 0.0

        # Simple Jaccard similarity
        pattern_set = set(
            word.lower() for symptom in self.symptoms for word in symptom.split()
        )
        symptom_set = set(
            word.lower() for symptom in symptoms for word in symptom.split()
        )

        intersection = len(pattern_set & symptom_set)
        union = len(pattern_set | symptom_set)

        return intersection / union if union > 0 else 0.0


@dataclass
class ComponentFailure:
    """Represents known failure modes for specific components"""

    component_type: str  # e.g., "AMS1117-3.3"
    manufacturer: str
    failure_mode: str
    failure_rate: float  # Failures per million hours
    symptoms: List[str]
    root_causes: List[str]
    environmental_factors: List[str]  # Temperature, humidity, vibration
    mitigation: List[str]
    references: List[str] = None


class DebugKnowledgeBase:
    """Manages debugging knowledge and historical patterns"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("memory-bank/debugging/debug_kb.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self._load_default_patterns()

    def _init_database(self):
        """Initialize SQLite database for pattern storage"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        # Create tables
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS debug_patterns (
                pattern_id TEXT PRIMARY KEY,
                category TEXT,
                symptoms TEXT,  -- JSON array
                root_cause TEXT,
                solutions TEXT,  -- JSON array
                component_types TEXT,  -- JSON array
                occurrence_count INTEGER DEFAULT 1,
                success_rate REAL DEFAULT 1.0,
                typical_measurements TEXT,  -- JSON object
                reference_docs TEXT,  -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS component_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_type TEXT,
                manufacturer TEXT,
                failure_mode TEXT,
                failure_rate REAL,
                symptoms TEXT,  -- JSON array
                root_causes TEXT,  -- JSON array
                environmental_factors TEXT,  -- JSON array
                mitigation TEXT,  -- JSON array
                reference_docs TEXT,  -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS debug_sessions (
                session_id TEXT PRIMARY KEY,
                board_name TEXT,
                board_version TEXT,
                symptoms TEXT,  -- JSON array
                measurements TEXT,  -- JSON object
                root_cause TEXT,
                resolution TEXT,
                duration_minutes INTEGER,
                success BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_patterns_category ON debug_patterns(category);
            CREATE INDEX IF NOT EXISTS idx_components_type ON component_failures(component_type);
            CREATE INDEX IF NOT EXISTS idx_sessions_board ON debug_sessions(board_name);
        """
        )
        self.conn.commit()

    def _load_default_patterns(self):
        """Load default debugging patterns"""
        default_patterns = [
            DebugPattern(
                pattern_id=self._generate_pattern_id(["3.3V", "low", "regulator"]),
                category="power",
                symptoms=[
                    "3.3V rail reading low",
                    "Board draws excessive current",
                    "Regulator hot",
                ],
                root_cause="Overloaded voltage regulator",
                solutions=[
                    "Replace regulator with higher current rating",
                    "Add heat sink to regulator",
                    "Distribute load across multiple regulators",
                    "Reduce circuit current consumption",
                ],
                component_types=["AMS1117", "LM1117", "LD1117"],
                typical_measurements={
                    "3.3V_rail": 2.8,
                    "regulator_temp_c": 85,
                    "current_draw_ma": 1200,
                },
            ),
            DebugPattern(
                pattern_id=self._generate_pattern_id(["USB", "enumeration", "fail"]),
                category="digital",
                symptoms=[
                    "USB device not recognized",
                    "Enumeration fails",
                    "Device descriptor error",
                ],
                root_cause="USB differential pair signal integrity issue",
                solutions=[
                    "Match D+ and D- trace lengths within 0.1mm",
                    "Maintain 90Ω differential impedance",
                    "Add common mode choke",
                    "Verify crystal frequency (12MHz, 24MHz, or 48MHz)",
                    "Add 22-33Ω series resistors on D+ and D-",
                ],
                component_types=["USB_Connector", "Crystal", "STM32", "ESP32"],
                typical_measurements={"D+_voltage": 0, "D-_voltage": 0, "VBUS": 5.0},
            ),
            DebugPattern(
                pattern_id=self._generate_pattern_id(["I2C", "no", "ACK"]),
                category="digital",
                symptoms=["I2C NACK", "No ACK from slave", "I2C timeout"],
                root_cause="I2C pull-up resistor issue",
                solutions=[
                    "Add 2.2kΩ to 10kΩ pull-up resistors on SDA and SCL",
                    "Verify I2C address (use I2C scanner)",
                    "Check voltage levels match between master and slave",
                    "Reduce I2C clock speed",
                    "Ensure proper ground connection between devices",
                ],
                component_types=["I2C_Device", "Microcontroller", "Sensor"],
                typical_measurements={
                    "SDA_high": 3.3,
                    "SCL_high": 3.3,
                    "pullup_resistance": 4700,
                },
            ),
            DebugPattern(
                pattern_id=self._generate_pattern_id(
                    ["oscillation", "power", "unstable"]
                ),
                category="power",
                symptoms=[
                    "Power rail oscillating",
                    "Unstable output voltage",
                    "Audible noise from regulator",
                ],
                root_cause="Incorrect output capacitor ESR",
                solutions=[
                    "Use capacitor with ESR in regulator's stable range",
                    "Add 10μF ceramic in parallel with electrolytic",
                    "Check PCB layout for long feedback traces",
                    "Add feedforward capacitor in feedback network",
                ],
                component_types=["LDO", "Buck_Converter", "Boost_Converter"],
                typical_measurements={"oscillation_freq_khz": 50, "ripple_vpp": 0.5},
            ),
            DebugPattern(
                pattern_id=self._generate_pattern_id(["ESD", "damage", "input"]),
                category="power",
                symptoms=[
                    "Component fails after handling",
                    "Intermittent failures",
                    "Input protection damaged",
                ],
                root_cause="ESD damage to semiconductor",
                solutions=[
                    "Add TVS diodes on all external interfaces",
                    "Implement proper ESD protection (IEC 61000-4-2)",
                    "Add series resistors to limit current",
                    "Use ESD-protected components",
                    "Ensure proper chassis grounding",
                ],
                component_types=["MOSFET", "IC", "Connector"],
                typical_measurements={
                    "input_impedance": "open",
                    "leakage_current_ua": 1000,
                },
            ),
        ]

        for pattern in default_patterns:
            self.add_pattern(pattern)

    def _generate_pattern_id(self, keywords: List[str]) -> str:
        """Generate unique pattern ID from keywords"""
        text = "_".join(sorted(keywords)).lower()
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def add_pattern(self, pattern: DebugPattern) -> bool:
        """Add or update a debugging pattern"""
        try:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO debug_patterns 
                (pattern_id, category, symptoms, root_cause, solutions, component_types,
                 occurrence_count, success_rate, typical_measurements, reference_docs, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    pattern.pattern_id,
                    pattern.category,
                    json.dumps(pattern.symptoms),
                    pattern.root_cause,
                    json.dumps(pattern.solutions),
                    json.dumps(pattern.component_types),
                    pattern.occurrence_count,
                    pattern.success_rate,
                    (
                        json.dumps(pattern.typical_measurements)
                        if pattern.typical_measurements
                        else None
                    ),
                    json.dumps(pattern.references) if pattern.references else None,
                ),
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding pattern: {e}")
            return False

    def search_patterns(
        self,
        symptoms: List[str],
        category: Optional[str] = None,
        min_similarity: float = 0.3,
    ) -> List[Tuple[DebugPattern, float]]:
        """Search for patterns matching given symptoms"""
        query = "SELECT * FROM debug_patterns"
        params = []

        if category:
            query += " WHERE category = ?"
            params.append(category)

        cursor = self.conn.execute(query, params)
        matches = []

        for row in cursor:
            pattern = DebugPattern(
                pattern_id=row["pattern_id"],
                category=row["category"],
                symptoms=json.loads(row["symptoms"]),
                root_cause=row["root_cause"],
                solutions=json.loads(row["solutions"]),
                component_types=json.loads(row["component_types"]),
                occurrence_count=row["occurrence_count"],
                success_rate=row["success_rate"],
                typical_measurements=(
                    json.loads(row["typical_measurements"])
                    if row["typical_measurements"]
                    else None
                ),
                references=(
                    json.loads(row["reference_docs"]) if row["reference_docs"] else None
                ),
            )

            similarity = pattern.matches_symptoms(symptoms)
            if similarity >= min_similarity:
                matches.append((pattern, similarity))

        # Sort by similarity and success rate
        matches.sort(key=lambda x: (x[1], x[0].success_rate), reverse=True)
        return matches

    def add_component_failure(self, failure: ComponentFailure) -> bool:
        """Add known component failure mode"""
        try:
            self.conn.execute(
                """
                INSERT INTO component_failures 
                (component_type, manufacturer, failure_mode, failure_rate, symptoms,
                 root_causes, environmental_factors, mitigation, reference_docs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    failure.component_type,
                    failure.manufacturer,
                    failure.failure_mode,
                    failure.failure_rate,
                    json.dumps(failure.symptoms),
                    json.dumps(failure.root_causes),
                    json.dumps(failure.environmental_factors),
                    json.dumps(failure.mitigation),
                    json.dumps(failure.references) if failure.references else None,
                ),
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding component failure: {e}")
            return False

    def get_component_failures(self, component_type: str) -> List[ComponentFailure]:
        """Get known failure modes for a component type"""
        cursor = self.conn.execute(
            "SELECT * FROM component_failures WHERE component_type LIKE ?",
            (f"%{component_type}%",),
        )

        failures = []
        for row in cursor:
            failure = ComponentFailure(
                component_type=row["component_type"],
                manufacturer=row["manufacturer"],
                failure_mode=row["failure_mode"],
                failure_rate=row["failure_rate"],
                symptoms=json.loads(row["symptoms"]),
                root_causes=json.loads(row["root_causes"]),
                environmental_factors=json.loads(row["environmental_factors"]),
                mitigation=json.loads(row["mitigation"]),
                references=(
                    json.loads(row["reference_docs"]) if row["reference_docs"] else None
                ),
            )
            failures.append(failure)

        return failures

    def record_debug_session(self, session_data: Dict[str, Any]) -> bool:
        """Record a completed debugging session for future reference"""
        try:
            self.conn.execute(
                """
                INSERT INTO debug_sessions 
                (session_id, board_name, board_version, symptoms, measurements,
                 root_cause, resolution, duration_minutes, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_data["session_id"],
                    session_data["board_name"],
                    session_data.get("board_version", "1.0"),
                    json.dumps(session_data.get("symptoms", [])),
                    json.dumps(session_data.get("measurements", {})),
                    session_data.get("root_cause", ""),
                    session_data.get("resolution", ""),
                    session_data.get("duration_minutes", 0),
                    session_data.get("success", False),
                ),
            )
            self.conn.commit()

            # Update pattern statistics if similar pattern exists
            if session_data.get("success") and session_data.get("symptoms"):
                patterns = self.search_patterns(session_data["symptoms"])
                if patterns:
                    best_pattern = patterns[0][0]
                    self.conn.execute(
                        """
                        UPDATE debug_patterns 
                        SET occurrence_count = occurrence_count + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE pattern_id = ?
                    """,
                        (best_pattern.pattern_id,),
                    )
                    self.conn.commit()

            return True
        except Exception as e:
            print(f"Error recording session: {e}")
            return False

    def get_similar_sessions(
        self, board_name: str, symptoms: List[str], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar debugging sessions from history"""
        # First try exact board matches
        cursor = self.conn.execute(
            "SELECT * FROM debug_sessions WHERE board_name = ? ORDER BY created_at DESC LIMIT ?",
            (board_name, limit * 2),
        )

        sessions = []
        for row in cursor:
            session_symptoms = json.loads(row["symptoms"])
            # Simple similarity check
            if any(s in " ".join(symptoms) for s in session_symptoms):
                sessions.append(
                    {
                        "session_id": row["session_id"],
                        "board_name": row["board_name"],
                        "symptoms": session_symptoms,
                        "root_cause": row["root_cause"],
                        "resolution": row["resolution"],
                        "success": row["success"],
                        "created_at": row["created_at"],
                    }
                )

        return sessions[:limit]
